from app.core.supabase import supabase
from datetime import datetime

def upsert_user(
    *,
    user_id: str,
    email: str,
    full_name: str | None = None,
    avatar_url: str | None = None,
):
    try:
        # 1️⃣ Check if user exists
        existing = (
            supabase
            .table("users")
            .select("user_id")
            .eq("user_id", user_id)
            .execute()
        )

        # 2️⃣ Update if exists
        if existing.data and len(existing.data) > 0:
            response = (
                supabase
                .table("users")
                .update({
                    "email": email,
                    "full_name": full_name,
                    "avatar_url": avatar_url,
                })
                .eq("user_id", user_id)
                .execute()
            )
        else:
            # 3️⃣ Insert if new
            response = (
                supabase
                .table("users")
                .insert({
                    "user_id": user_id,
                    "email": email,
                    "full_name": full_name,
                    "avatar_url": avatar_url,
                    "subscribed_plan" : 0,
                    "created_at": datetime.utcnow().isoformat(),
                })
                .execute()
            )

        return response.data

    except Exception as e:
        # Supabase throws real errors here
        raise Exception(f"Supabase operation failed: {e}")

def get_user_plan(user_id: str):
    response = (
        supabase
        .table("users")
        .select("subscribed_plan")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    return response.data["subscribed_plan"]
