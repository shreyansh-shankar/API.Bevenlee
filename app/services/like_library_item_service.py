from app.core.supabase import supabase


class ItemNotFoundError(Exception):
    pass


def toggle_like(user_id: str, item_id: str) -> dict:
    """
    Toggle a like on a library item.
    Returns { "liked": bool, "like_count": int }
    """

    # Verify item exists
    item = (
        supabase.table("library_items")
        .select("item_id")
        .eq("item_id", item_id)
        .single()
        .execute()
    ).data

    if not item:
        raise ItemNotFoundError("Library item not found")

    # Check if already liked
    existing = (
        supabase.table("library_likes")
        .select("like_id")
        .eq("item_id", item_id)
        .eq("user_id", user_id)
        .execute()
    ).data or []

    if existing:
        # Unlike
        supabase.table("library_likes") \
            .delete() \
            .eq("item_id", item_id) \
            .eq("user_id", user_id) \
            .execute()
        liked = False
    else:
        # Like
        supabase.table("library_likes").insert({
            "item_id": item_id,
            "user_id": user_id,
        }).execute()
        liked = True

    # Return updated like count
    count_result = (
        supabase.table("library_likes")
        .select("like_id", count="exact")
        .eq("item_id", item_id)
        .execute()
    )

    return {
        "liked": liked,
        "like_count": count_result.count or 0,
    }