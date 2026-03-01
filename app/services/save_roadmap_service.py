from app.core.supabase import supabase

def save_roadmap(roadmap_id: str, title: str, description: str | None, course_ids: list[str]):
    res = (
        supabase
        .table("roadmaps")
        .update({
            "title": title,
            "description": description,
            "course_ids": course_ids,
        })
        .eq("roadmap_id", roadmap_id)
        .execute()
    )

    return res.data[0] if res.data else None