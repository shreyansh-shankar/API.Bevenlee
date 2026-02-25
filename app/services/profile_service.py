from app.core.supabase import supabase


def get_user_profile(user_id: str):
    """
    Fetch user profile info.
    Returns None if user not found.
    """

    res = (
        supabase
        .table("users")
        .select(
            "user_id, email, full_name, avatar_url, subscribed_plan, created_at"
        )
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    user = res.data

    if not user:
        return None

    return user



def update_user_profile(
    user_id: str,
    *,
    full_name: str | None = None,
    avatar_url: str | None = None,
):
    """
    Update profile fields.
    Only updates provided values.
    """

    update_data = {}

    if full_name is not None:
        update_data["full_name"] = full_name

    if avatar_url is not None:
        update_data["avatar_url"] = avatar_url

    if not update_data:
        return None

    res = (
        supabase
        .table("users")
        .update(update_data)
        .eq("user_id", user_id)
        .execute()
    )

    return res.data