from app.core.supabase import supabase

def get_roadmaps_by_user(user_id: str):
    res = (
        supabase
        .table("roadmaps")
        .select("roadmap_id, title, description, course_ids, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return res.data or []