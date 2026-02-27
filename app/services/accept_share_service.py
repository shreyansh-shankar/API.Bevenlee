from app.core.supabase import supabase
from app.services.add_course_service import get_user_plan
from app.core.enforce_topic_limit import enforce_topic_limit
from datetime import datetime, timezone
import uuid
from app.config.subscription import PLAN_LIMITS

def generate_id() -> str:
    return str(uuid.uuid4())


class ShareExpiredError(Exception):
    pass

class PlanUpgradeRequired(Exception):
    pass

class CourseLimitExceeded(Exception):
    pass

class TopicLimitExceeded(Exception):
    pass


def _get_plan_course_limit(plan_id: int) -> int:
    limits = PLAN_LIMITS.get(plan_id, {})
    max_courses = limits.get("max_courses", 3)
    return max_courses if max_courses != -1 else float("inf")


def accept_share(token: str, recipient_user_id: str) -> dict:
    """
    Clone a shared course + all its data + whiteboards for the recipient user.
    Returns { "course_id": new_course_id }
    """

    # ── 1. Resolve the share token ──────────────────────────────────────────
    share = (
        supabase.table("course_shares")
        .select("share_id, course_id, expires_at")
        .eq("token", token)
        .single()
        .execute()
    )

    if not share.data:
        raise ValueError("Share link not found")

    row = share.data

    if row["expires_at"]:
        expires_dt = datetime.fromisoformat(row["expires_at"]).astimezone(timezone.utc)
        if datetime.now(timezone.utc) > expires_dt:
            raise ShareExpiredError("This share link has expired")

    source_course_id = row["course_id"]

    # ── 2. Plan checks for recipient ────────────────────────────────────────
    plan_id = get_user_plan(recipient_user_id)

    # ← ADD THIS
    if plan_id == 0:
        raise PlanUpgradeRequired("Course sharing is only available on Pro and above")

    # Check course limit
    existing_courses = (
        supabase.table("courses")
        .select("course_id", count="exact")
        .eq("user_id", recipient_user_id)
        .execute()
    )
    course_limit = _get_plan_course_limit(plan_id)
    if (existing_courses.count or 0) >= course_limit:
        raise CourseLimitExceeded("You have reached your course limit")

    # Fetch source topics to check topic limit
    source_topics = (
        supabase.table("topics")
        .select("*")
        .eq("course_id", source_course_id)
        .execute()
    ).data or []

    # Reuse your existing enforce_topic_limit — it raises PlanLimitExceeded
    try:
        enforce_topic_limit(plan_id, source_topics)
    except Exception:
        raise TopicLimitExceeded("This course has more topics than your plan allows")

    # ── 3. Clone course row ─────────────────────────────────────────────────
    source_course = (
        supabase.table("courses")
        .select("*")
        .eq("course_id", source_course_id)
        .single()
        .execute()
    ).data

    if not source_course:
        raise ValueError("Source course not found")

    new_course_id = generate_id()

    supabase.table("courses").insert({
        "course_id": new_course_id,
        "user_id": recipient_user_id,
        "title": source_course["title"],
        "type": source_course["type"],
        "status": source_course["status"],
        "priority": source_course["priority"],
        "purpose": source_course.get("purpose"),
        "projects_enabled": source_course.get("projects_enabled", False),
        "assignments_enabled": source_course.get("assignments_enabled", False),
    }).execute()

    # ── 4. Clone topics + subtopics, build topic_id mapping ─────────────────
    # topic_id_map: old_topic_id → new_topic_id (needed for whiteboard copy)
    topic_id_map: dict[str, str] = {}

    for topic in source_topics:
        new_topic_id = generate_id()
        topic_id_map[topic["topic_id"]] = new_topic_id

        supabase.table("topics").insert({
            "topic_id": new_topic_id,
            "course_id": new_course_id,
            "title": topic["title"],
            "status": topic["status"],
            "position": topic["position"],
        }).execute()

        # Clone subtopics for this topic
        subtopics = (
            supabase.table("subtopics")
            .select("*")
            .eq("topic_id", topic["topic_id"])
            .execute()
        ).data or []

        for sub in subtopics:
            supabase.table("subtopics").insert({
                "subtopic_id": generate_id(),
                "topic_id": new_topic_id,
                "title": sub["title"],
                "is_completed": False,   # reset completion for new owner
                "position": sub["position"],
            }).execute()

    # ── 5. Clone resources ──────────────────────────────────────────────────
    resources = (
        supabase.table("resources")
        .select("*")
        .eq("course_id", source_course_id)
        .execute()
    ).data or []

    for r in resources:
        # Remap topic_id if the resource is linked to a specific topic
        new_topic_ref = topic_id_map.get(r.get("topic_id")) if r.get("topic_id") else None

        supabase.table("resources").insert({
            "resource_id": generate_id(),
            "course_id": new_course_id,
            "topic_id": new_topic_ref,
            "title": r["title"],
            "url": r["url"],
        }).execute()

    # ── 6. Clone projects ───────────────────────────────────────────────────
    projects = (
        supabase.table("projects")
        .select("*")
        .eq("course_id", source_course_id)
        .execute()
    ).data or []

    for p in projects:
        supabase.table("projects").insert({
            "project_id": generate_id(),
            "course_id": new_course_id,
            "title": p["title"],
            "status": "planned",    # reset status for new owner
            "description": p.get("description"),
        }).execute()

    # ── 7. Clone assignments ────────────────────────────────────────────────
    assignments = (
        supabase.table("assignments")
        .select("*")
        .eq("course_id", source_course_id)
        .execute()
    ).data or []

    for a in assignments:
        supabase.table("assignments").insert({
            "assignment_id": generate_id(),
            "course_id": new_course_id,
            "title": a["title"],
            "status": "pending",    # reset status for new owner
            "description": a.get("description"),
        }).execute()

    # ── 8. Clone whiteboards from storage ───────────────────────────────────
    for old_topic_id, new_topic_id in topic_id_map.items():
        old_path = f"whiteboard-{old_topic_id}.json"
        new_path = f"whiteboard-{new_topic_id}.json"

        try:
            # Download the source whiteboard
            response = supabase.storage.from_("whiteboards").download(old_path)
            if response:
                # Upload under the new topic's path
                supabase.storage.from_("whiteboards").upload(
                    path=new_path,
                    file=response,
                    file_options={"content-type": "application/json", "upsert": "true"},
                )
        except Exception:
            # Whiteboard may not exist for every topic — that's fine, skip silently
            pass

    return {"course_id": new_course_id}