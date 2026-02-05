from app.core.supabase import supabase
from datetime import datetime

def create_course(
    *,
    user_id: str,
    title: str,
    type: str,
    purpose: str | None,
    status: str,
    priority: str,
):
    try:
        response = (
            supabase
            .table("courses")
            .insert({
                "user_id": user_id,
                "title": title,
                "purpose": purpose,
                "type": type,
                "status": status,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
            })
            .execute()
        )

        return response.data

    except Exception as e:
        raise Exception(f"Supabase operation failed: {e}")
