from app.core.supabase import supabase
from app.services.add_course_service import get_user_plan
from app.services.accept_share_service import accept_share as accept_course_share
from datetime import datetime, timezone
import uuid

def generate_id() -> str:
    return str(uuid.uuid4())

class ShareExpiredError(Exception):
    pass

class PlanUpgradeRequired(Exception):
    pass

class CourseLimitExceeded(Exception):
    pass


def accept_roadmap_share(token: str, recipient_user_id: str) -> dict:
    """
    Clone a shared roadmap + all its courses for the recipient.
    Returns { "roadmap_id": new_roadmap_id }
    """

    # ── 1. Resolve the share token ──────────────────────────────────────────
    share = (
        supabase.table("roadmap_shares")
        .select("share_id, roadmap_id, expires_at, whiteboards")
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

    source_roadmap_id = row["roadmap_id"]
    clone_whiteboards = row["whiteboards"]

    # ── 2. Plan check ───────────────────────────────────────────────────────
    plan_id = get_user_plan(recipient_user_id)

    if plan_id == 0:
        raise PlanUpgradeRequired("Roadmap sharing is only available on Pro and above")

    # ── 3. Fetch source roadmap ─────────────────────────────────────────────
    source_roadmap = (
        supabase.table("roadmaps")
        .select("*")
        .eq("roadmap_id", source_roadmap_id)
        .single()
        .execute()
    ).data

    if not source_roadmap:
        raise ValueError("Source roadmap not found")

    source_course_ids: list[str] = source_roadmap.get("course_ids") or []

    # ── 4. Check recipient has room for all courses ─────────────────────────
    from app.services.accept_share_service import _get_plan_course_limit
    existing_courses = (
        supabase.table("courses")
        .select("course_id", count="exact")
        .eq("user_id", recipient_user_id)
        .execute()
    )
    course_limit = _get_plan_course_limit(plan_id)
    current_count = existing_courses.count or 0

    if current_count + len(source_course_ids) > course_limit:
        raise CourseLimitExceeded(
            f"This roadmap contains {len(source_course_ids)} courses but you only have "
            f"{int(course_limit) - current_count} slot(s) remaining."
        )

    # ── 5. Clone each course via existing accept_share logic ────────────────
    # We need per-course share tokens — but we're calling the service directly.
    # Instead, clone courses manually using the same pattern as accept_share_service
    # but driven from course_ids, not a token.
    from app.services.accept_share_service import (
        generate_id as _gen_id,
    )
    from app.core.enforce_topic_limit import enforce_topic_limit
    from app.services.accept_share_service import TopicLimitExceeded

    old_to_new_course_id: dict[str, str] = {}

    for source_course_id in source_course_ids:
        source_course = (
            supabase.table("courses")
            .select("*")
            .eq("course_id", source_course_id)
            .single()
            .execute()
        ).data

        if not source_course:
            continue  # course was deleted — skip it

        new_course_id = generate_id()
        old_to_new_course_id[source_course_id] = new_course_id

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

        # Clone topics + subtopics
        source_topics = (
            supabase.table("topics")
            .select("*")
            .eq("course_id", source_course_id)
            .execute()
        ).data or []

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
                    "is_completed": False,
                    "position": sub["position"],
                }).execute()

        # Clone resources
        resources = (
            supabase.table("resources")
            .select("*")
            .eq("course_id", source_course_id)
            .execute()
        ).data or []

        for r in resources:
            new_topic_ref = topic_id_map.get(r.get("topic_id")) if r.get("topic_id") else None
            supabase.table("resources").insert({
                "resource_id": generate_id(),
                "course_id": new_course_id,
                "topic_id": new_topic_ref,
                "title": r["title"],
                "url": r["url"],
            }).execute()

        # Clone projects
        for p in (supabase.table("projects").select("*").eq("course_id", source_course_id).execute()).data or []:
            supabase.table("projects").insert({
                "project_id": generate_id(),
                "course_id": new_course_id,
                "title": p["title"],
                "status": "planned",
                "description": p.get("description"),
            }).execute()

        # Clone assignments
        for a in (supabase.table("assignments").select("*").eq("course_id", source_course_id).execute()).data or []:
            supabase.table("assignments").insert({
                "assignment_id": generate_id(),
                "course_id": new_course_id,
                "title": a["title"],
                "status": "pending",
                "description": a.get("description"),
            }).execute()

        # Clone whiteboards (conditional)
        if clone_whiteboards:
            for old_topic_id, new_topic_id in topic_id_map.items():
                try:
                    response = supabase.storage.from_("whiteboards").download(
                        f"whiteboard-{old_topic_id}.json"
                    )
                    if response:
                        supabase.storage.from_("whiteboards").upload(
                            path=f"whiteboard-{new_topic_id}.json",
                            file=response,
                            file_options={"content-type": "application/json", "upsert": "true"},
                        )
                except Exception:
                    pass

    # ── 6. Clone roadmap row with remapped course_ids ───────────────────────
    new_course_ids = [
        old_to_new_course_id[cid]
        for cid in source_course_ids
        if cid in old_to_new_course_id  # skip deleted courses
    ]

    new_roadmap_id = generate_id()

    supabase.table("roadmaps").insert({
        "roadmap_id": new_roadmap_id,
        "user_id": recipient_user_id,
        "title": source_roadmap["title"],
        "description": source_roadmap.get("description"),
        "course_ids": new_course_ids,
    }).execute()

    return {"roadmap_id": new_roadmap_id}