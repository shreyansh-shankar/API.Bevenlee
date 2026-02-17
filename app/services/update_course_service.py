from app.core.supabase import supabase
from datetime import datetime

def update_course(course_id: str, updates: dict):
    try:
        response = (
            supabase
            .table("courses")
            .update(updates)
            .eq("course_id", course_id)
            .execute()
        )

        return response.data

    except Exception as e:
        raise Exception(f"Failed to update course: {e}")
