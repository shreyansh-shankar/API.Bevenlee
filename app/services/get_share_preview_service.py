from app.core.supabase import supabase
from datetime import datetime, timezone
from app.services.profile_service import get_user_profile

def get_share_preview(token: str) -> dict | None:
    """
    Public preview — no auth needed.
    Returns course metadata for the share landing page.
    """
    share = (
        supabase.table("course_shares")
        .select("share_id, course_id, created_by, expires_at")
        .eq("token", token)
        .single()
        .execute()
    )

    if not share.data:
        return None

    row = share.data

    # Check expiry
    is_expired = False
    if row["expires_at"]:
        expires_dt = datetime.fromisoformat(row["expires_at"]).astimezone(timezone.utc)
        is_expired = datetime.now(timezone.utc) > expires_dt

    # Fetch course
    course = (
        supabase.table("courses")
        .select("title, type, status")
        .eq("course_id", row["course_id"])
        .single()
        .execute()
    )

    if not course.data:
        return None

    # Count topics (non-deleted)
    topics = (
        supabase.table("topics")
        .select("topic_id", count="exact")
        .eq("course_id", row["course_id"])
        .execute()
    )

    # Count resources
    resources = (
        supabase.table("resources")
        .select("resource_id", count="exact")
        .eq("course_id", row["course_id"])
        .execute()
    )

    # Get creator display name from profiles (adjust table/column to match your schema)
    try:
        profile = get_user_profile(row["created_by"])
        creator_name = profile.get("full_name") or "Someone"
    except Exception:
        creator_name = "Someone"

    return {
        "course_title": course.data["title"],
        "course_type": course.data["type"],
        "course_status": course.data["status"],
        "topic_count": topics.count or 0,
        "resource_count": resources.count or 0,
        "created_by_name": creator_name,
        "expires_at": row["expires_at"],
        "is_expired": is_expired,
    }