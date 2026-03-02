from app.core.supabase import supabase
from datetime import datetime, timezone

def get_roadmap_share_preview(token: str) -> dict | None:
    share = (
        supabase.table("roadmap_shares")
        .select("share_id, roadmap_id, expires_at, whiteboards, created_by")
        .eq("token", token)
        .single()
        .execute()
    )

    if not share.data:
        return None

    row = share.data

    is_expired = False
    if row["expires_at"]:
        expires_dt = datetime.fromisoformat(row["expires_at"]).astimezone(timezone.utc)
        if datetime.now(timezone.utc) > expires_dt:
            is_expired = True

    # Fetch roadmap details
    roadmap = (
        supabase.table("roadmaps")
        .select("title, description, course_ids")
        .eq("roadmap_id", row["roadmap_id"])
        .single()
        .execute()
    ).data

    if not roadmap:
        return None

    course_count = len(roadmap.get("course_ids") or [])

    # Fetch creator display name
    creator = (
        supabase.table("profiles")
        .select("display_name")
        .eq("user_id", row["created_by"])
        .single()
        .execute()
    ).data

    created_by_name = (creator or {}).get("display_name", "Someone")

    return {
        "roadmap_title": roadmap["title"],
        "roadmap_description": roadmap.get("description"),
        "course_count": course_count,
        "created_by_name": created_by_name,
        "expires_at": row["expires_at"],
        "is_expired": is_expired,
        "whiteboards": row["whiteboards"],
    }