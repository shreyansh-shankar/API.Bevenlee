from app.core.supabase import supabase

def delete_course(course_id: str):
    try:
        response = (
            supabase
            .table("courses")
            .delete()
            .eq("course_id", course_id)
            .execute()
        )

        return response.data

    except Exception as e:
        raise Exception(f"Failed to delete course: {e}")
