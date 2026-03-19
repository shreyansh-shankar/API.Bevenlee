from app.core.supabase import supabase

PAGE_SIZE = 20


def get_library(
    user_id: str,
    item_type: str | None,   # "course" | "roadmap" | None (both)
    liked_only: bool,
    page: int,               # 1-based
) -> dict:
    """
    Return a paginated list of library items with like counts and
    whether the requesting user has liked each item.

    Returns:
        {
            "items": [...],
            "total": int,
            "page": int,
            "page_size": int,
            "has_next": bool,
        }
    """

    offset = (page - 1) * PAGE_SIZE

    # ── 1. Fetch liked item_ids for this user (needed for liked_only filter
    #       and for annotating results) ──────────────────────────────────────
    liked_rows = (
        supabase.table("library_likes")
        .select("item_id")
        .eq("user_id", user_id)
        .execute()
    ).data or []

    liked_item_ids: set[str] = {r["item_id"] for r in liked_rows}

    # ── 2. Build the base query ──────────────────────────────────────────────
    query = supabase.table("library_items").select(
        "item_id, item_type, source_id, added_by, is_admin_pick, whiteboards, title, description, created_at",
        count="exact",
    )

    if item_type in ("course", "roadmap"):
        query = query.eq("item_type", item_type)

    if liked_only:
        if not liked_item_ids:
            # User has no likes — return empty immediately
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": PAGE_SIZE,
                "has_next": False,
            }
        query = query.in_("item_id", list(liked_item_ids))

    # ── 3. Pagination + ordering ─────────────────────────────────────────────
    query = (
        query
        .order("created_at", desc=True)
        .range(offset, offset + PAGE_SIZE - 1)
    )

    result = query.execute()
    rows = result.data or []
    total = result.count or 0

    # ── 4. Fetch like counts for all returned items ──────────────────────────
    item_ids = [r["item_id"] for r in rows]
    like_counts: dict[str, int] = {}

    if item_ids:
        likes_result = (
            supabase.table("library_likes")
            .select("item_id", count="exact")
            .in_("item_id", item_ids)
            .execute()
        ).data or []

        # Count manually since supabase-py doesn't support GROUP BY
        for r in likes_result:
            iid = r["item_id"]
            like_counts[iid] = like_counts.get(iid, 0) + 1

    # ── 5. Annotate each item ────────────────────────────────────────────────
    items = []
    for row in rows:
        iid = row["item_id"]
        items.append({
            **row,
            "like_count": like_counts.get(iid, 0),
            "liked_by_me": iid in liked_item_ids,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "has_next": (offset + PAGE_SIZE) < total,
    }