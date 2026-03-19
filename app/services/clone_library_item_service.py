from app.core.supabase import supabase
from app.services.add_course_service import get_user_plan
from app.services.accept_share_service import (
    _get_plan_course_limit,
    TopicLimitExceeded,
)
from app.core.enforce_topic_limit import enforce_topic_limit
from datetime import datetime, timezone
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())


# ── Reusable errors (same names as share services for consistent HTTP mapping) ─
class PlanUpgradeRequired(Exception):
    pass


class CourseLimitExceeded(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


# ════════════════════════════════════════════════════════════════════════════════
# Internal helpers — identical clone logic extracted from accept_share_service
# but driven by source_id directly (no token), and with caller-controlled
# include_whiteboards flag (subject to what the library item allows).
# ════════════════════════════════════════════════════════════════════════════════

def _clone_course(
    source_course_id: str,
    recipient_user_id: str,
    clone_whiteboards: bool,
) -> str:
    """Clone a single course and return the new course_id."""

    source_course = (
        supabase.table("courses")
        .select("*")
        .eq("course_id", source_course_id)
        .single()
        .execute()
    ).data

    if not source_course:
        raise ValueError(f"Source course {source_course_id} not found")

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

    # Topics + subtopics
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

    # Resources
    for r in (supabase.table("resources").select("*").eq("course_id", source_course_id).execute()).data or []:
        new_topic_ref = topic_id_map.get(r.get("topic_id")) if r.get("topic_id") else None
        supabase.table("resources").insert({
            "resource_id": generate_id(),
            "course_id": new_course_id,
            "topic_id": new_topic_ref,
            "title": r["title"],
            "url": r["url"],
        }).execute()

    # Projects
    for p in (supabase.table("projects").select("*").eq("course_id", source_course_id).execute()).data or []:
        supabase.table("projects").insert({
            "project_id": generate_id(),
            "course_id": new_course_id,
            "title": p["title"],
            "status": "planned",
            "description": p.get("description"),
        }).execute()

    # Assignments
    for a in (supabase.table("assignments").select("*").eq("course_id", source_course_id).execute()).data or []:
        supabase.table("assignments").insert({
            "assignment_id": generate_id(),
            "course_id": new_course_id,
            "title": a["title"],
            "status": "pending",
            "description": a.get("description"),
        }).execute()

    # Whiteboards
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
                pass  # whiteboard may not exist for every topic — skip silently

    return new_course_id


# ════════════════════════════════════════════════════════════════════════════════
# Public entry points
# ════════════════════════════════════════════════════════════════════════════════

def clone_library_course(
    item_id: str,
    recipient_user_id: str,
    include_whiteboards: bool,
) -> dict:
    """
    Clone a library course item into the recipient's account.
    include_whiteboards is honoured only if the library item itself has
    whiteboards=True.
    Returns { "course_id": new_course_id }
    """

    # ── 1. Fetch library item ────────────────────────────────────────────────
    item = (
        supabase.table("library_items")
        .select("item_id, item_type, source_id, whiteboards")
        .eq("item_id", item_id)
        .eq("item_type", "course")
        .single()
        .execute()
    ).data

    if not item:
        raise ItemNotFoundError("Library item not found")

    # Recipient can only include whiteboards if the library item allows it
    clone_whiteboards = include_whiteboards and item["whiteboards"]

    # ── 2. Plan checks ───────────────────────────────────────────────────────
    plan_id = get_user_plan(recipient_user_id)

    if plan_id == 0:
        raise PlanUpgradeRequired("Library access is only available on Pro and above")

    existing = (
        supabase.table("courses")
        .select("course_id", count="exact")
        .eq("user_id", recipient_user_id)
        .execute()
    )
    course_limit = _get_plan_course_limit(plan_id)
    if (existing.count or 0) >= course_limit:
        raise CourseLimitExceeded("You have reached your course limit")

    source_topics = (
        supabase.table("topics")
        .select("*")
        .eq("course_id", item["source_id"])
        .execute()
    ).data or []

    try:
        enforce_topic_limit(plan_id, source_topics)
    except Exception:
        raise TopicLimitExceeded("This course has more topics than your plan allows")

    # ── 3. Clone ─────────────────────────────────────────────────────────────
    new_course_id = _clone_course(item["source_id"], recipient_user_id, clone_whiteboards)

    return {"course_id": new_course_id}


def clone_library_roadmap(
    item_id: str,
    recipient_user_id: str,
    include_whiteboards: bool,
) -> dict:
    """
    Clone a library roadmap item (and all its courses) into the recipient's account.
    include_whiteboards is honoured only if the library item itself has
    whiteboards=True.
    Returns { "roadmap_id": new_roadmap_id }
    """

    # ── 1. Fetch library item ────────────────────────────────────────────────
    item = (
        supabase.table("library_items")
        .select("item_id, item_type, source_id, whiteboards")
        .eq("item_id", item_id)
        .eq("item_type", "roadmap")
        .single()
        .execute()
    ).data

    if not item:
        raise ItemNotFoundError("Library item not found")

    clone_whiteboards = include_whiteboards and item["whiteboards"]

    # ── 2. Plan check ────────────────────────────────────────────────────────
    plan_id = get_user_plan(recipient_user_id)

    if plan_id == 0:
        raise PlanUpgradeRequired("Library access is only available on Pro and above")

    # ── 3. Fetch source roadmap ──────────────────────────────────────────────
    source_roadmap = (
        supabase.table("roadmaps")
        .select("*")
        .eq("roadmap_id", item["source_id"])
        .single()
        .execute()
    ).data

    if not source_roadmap:
        raise ValueError("Source roadmap not found")

    source_course_ids: list[str] = source_roadmap.get("course_ids") or []

    # ── 4. Course-limit check ────────────────────────────────────────────────
    existing = (
        supabase.table("courses")
        .select("course_id", count="exact")
        .eq("user_id", recipient_user_id)
        .execute()
    )
    course_limit = _get_plan_course_limit(plan_id)
    current_count = existing.count or 0

    if current_count + len(source_course_ids) > course_limit:
        raise CourseLimitExceeded(
            f"This roadmap contains {len(source_course_ids)} courses but you only have "
            f"{int(course_limit) - current_count} slot(s) remaining."
        )

    # ── 5. Clone each course ─────────────────────────────────────────────────
    old_to_new: dict[str, str] = {}

    for source_course_id in source_course_ids:
        try:
            new_course_id = _clone_course(source_course_id, recipient_user_id, clone_whiteboards)
            old_to_new[source_course_id] = new_course_id
        except ValueError:
            pass  # course was deleted — skip it

    # ── 6. Clone roadmap row with remapped course_ids ────────────────────────
    new_course_ids = [
        old_to_new[cid] for cid in source_course_ids if cid in old_to_new
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