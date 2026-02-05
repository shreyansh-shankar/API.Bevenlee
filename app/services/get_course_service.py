from app.core.supabase import supabase

def get_courses_by_user(user_id: str):
    try:
        response = (
            supabase
            .table("courses")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data

    except Exception as e:
        raise Exception(f"Failed to fetch courses: {e}")
