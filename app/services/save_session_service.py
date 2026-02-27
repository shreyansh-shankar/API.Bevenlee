from app.core.supabase import supabase
import uuid

def save_session(user_id: str, topic_id: str, started_at: str, duration_minutes: int):
    session_id = str(uuid.uuid4())
    
    result = supabase.table("study_sessions").insert({
        "session_id": session_id,
        "user_id": user_id,
        "topic_id": topic_id,
        "started_at": started_at,
        "duration_minutes": duration_minutes,
    }).execute()

    return result.data[0] if result.data else None