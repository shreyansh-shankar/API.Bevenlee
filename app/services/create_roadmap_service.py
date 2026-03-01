from app.core.supabase import supabase
import uuid

def create_roadmap(user_id: str, title: str, description: str | None = None):
    roadmap_id = str(uuid.uuid4())

    res = supabase.table("roadmaps").insert({
        "roadmap_id": roadmap_id,
        "user_id": user_id,
        "title": title,
        "description": description,
        "course_ids": [],
    }).execute()

    return res.data[0] if res.data else None