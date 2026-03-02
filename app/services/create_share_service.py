from app.core.supabase import supabase
from datetime import datetime, timedelta, timezone
import secrets


def generate_token() -> str:
    # 24-char URL-safe token, e.g. "aB3xKq9mZ2pLwR7nYcVt4uDs"
    return secrets.token_urlsafe(18)


def create_share(user_id: str, course_id: str, expiry: str, whiteboards: bool = False) -> dict:
    """
    Create a share link for a course.
    expiry: "never" | "7d" | "30d"
    """
    # Verify the course belongs to this user
    course = (
        supabase.table("courses")
        .select("course_id, title")
        .eq("course_id", course_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not course.data:
        raise ValueError("Course not found or not owned by user")

    expires_at = None
    if expiry == "7d":
        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    elif expiry == "30d":
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    token = generate_token()

    result = supabase.table("course_shares").insert({
        "course_id": course_id,
        "created_by": user_id,
        "token": token,
        "expires_at": expires_at,
        "whiteboards": whiteboards,
    }).execute()

    row = result.data[0]

    return {
        "token": row["token"],
        "expires_at": row["expires_at"],
        "whiteboards": row["whiteboards"],
    }