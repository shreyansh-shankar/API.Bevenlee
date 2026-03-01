from app.core.supabase import supabase

def delete_roadmap(roadmap_id: str):
    supabase.table("roadmaps").delete().eq("roadmap_id", roadmap_id).execute()