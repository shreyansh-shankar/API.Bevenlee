from app.core.supabase import supabase
from datetime import datetime, timedelta, timezone
import secrets

def generate_token() -> str:
    return secrets.token_urlsafe(18)

def create_roadmap_share(user_id: str, roadmap_id: str, expiry: str, whiteboards: bool = False) -> dict:
    # Verify roadmap belongs to this user
    roadmap = (
        supabase.table("roadmaps")
        .select("roadmap_id, title")
        .eq("roadmap_id", roadmap_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not roadmap.data:
        raise ValueError("Roadmap not found or not owned by user")

    expires_at = None
    if expiry == "7d":
        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    elif expiry == "30d":
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    token = generate_token()

    result = supabase.table("roadmap_shares").insert({
        "roadmap_id": roadmap_id,
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