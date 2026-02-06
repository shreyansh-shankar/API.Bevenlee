from app.core.supabase import supabase
from datetime import datetime
import uuid

def generate_id():
    return str(uuid.uuid4())

def save_course(course_id: str, payload: dict):
    """
    Save or update course aggregate in supabase
    """

    # ----------------- 1. Update course -----------------
    course_data = payload["course"]
    supabase.table("courses").update({
        "title": course_data.get("title"),
        "type": course_data.get("type"),
        "status": course_data.get("status"),
        "priority": course_data.get("priority"),
        "purpose": course_data.get("purpose"),
        "projects_enabled": course_data.get("projects_enabled", False),
        "assignments_enabled": course_data.get("assignments_enabled", False),
    }).eq("course_id", course_id).execute()

    # ----------------- 2. Sync topics & subtopics -----------------
    topics = payload.get("topics", [])
    existing_topics = supabase.table("topics").select("topic_id").eq("course_id", course_id).execute().data or []
    existing_topic_ids = [t["topic_id"] for t in existing_topics]
    incoming_topic_ids = [t.get("topic_id") for t in topics if t.get("topic_id")]

    # Delete removed topics
    to_delete = [tid for tid in existing_topic_ids if tid not in incoming_topic_ids]
    if to_delete:
        supabase.table("topics").delete().in_("topic_id", to_delete).execute()
        supabase.table("subtopics").delete().in_("topic_id", to_delete).execute()

    for t in topics:
        topic_id = t.get("topic_id") or generate_id()
        supabase.table("topics").upsert({
            "topic_id": topic_id,
            "course_id": course_id,
            "title": t["title"],
            "status": t["status"],
            "position": t["position"],
        }, on_conflict="topic_id").execute()

        # Sync subtopics
        subtopics = t.get("subtopics", [])
        existing_subs = supabase.table("subtopics").select("subtopic_id").eq("topic_id", topic_id).execute().data or []
        existing_sub_ids = [st["subtopic_id"] for st in existing_subs]
        incoming_sub_ids = [st.get("subtopic_id") for st in subtopics if st.get("subtopic_id")]

        # Delete removed subtopics
        to_delete_sub = [sid for sid in existing_sub_ids if sid not in incoming_sub_ids]
        if to_delete_sub:
            supabase.table("subtopics").delete().in_("subtopic_id", to_delete_sub).execute()

        # Upsert subtopics
        for st in subtopics:
            sub_id = st.get("subtopic_id") or generate_id()
            supabase.table("subtopics").upsert({
                "subtopic_id": sub_id,
                "topic_id": topic_id,
                "title": st["title"],
                "is_completed": st["is_completed"],
                "position": st["position"],
            }, on_conflict="subtopic_id").execute()

    # ----------------- 3. Sync resources -----------------
    resources = payload.get("resources", [])
    existing_res = supabase.table("resources").select("resource_id").eq("course_id", course_id).execute().data or []
    existing_res_ids = [r["resource_id"] for r in existing_res]
    incoming_res_ids = [r.get("resource_id") for r in resources if r.get("resource_id")]

    to_delete_res = [rid for rid in existing_res_ids if rid not in incoming_res_ids]
    if to_delete_res:
        supabase.table("resources").delete().in_("resource_id", to_delete_res).execute()

    for r in resources:
        res_id = r.get("resource_id") or generate_id()
        supabase.table("resources").upsert({
            "resource_id": res_id,
            "course_id": course_id,
            "topic_id": r.get("topic_id"),
            "title": r["title"],
            "url": r["url"],
        }, on_conflict="resource_id").execute()

    # ----------------- 4. Sync projects -----------------
    projects = payload.get("projects", [])
    existing_proj = supabase.table("projects").select("project_id").eq("course_id", course_id).execute().data or []
    existing_proj_ids = [p["project_id"] for p in existing_proj]
    incoming_proj_ids = [p.get("project_id") for p in projects if p.get("project_id")]

    to_delete_proj = [pid for pid in existing_proj_ids if pid not in incoming_proj_ids]
    if to_delete_proj:
        supabase.table("projects").delete().in_("project_id", to_delete_proj).execute()

    for p in projects:
        proj_id = p.get("project_id") or generate_id()
        supabase.table("projects").upsert({
            "project_id": proj_id,
            "course_id": course_id,
            "title": p["title"],
            "status": p["status"],
            "description": p.get("description"),
        }, on_conflict="project_id").execute()

    # ----------------- 5. Sync assignments -----------------
    assignments = payload.get("assignments", [])
    existing_assign = supabase.table("assignments").select("assignment_id").eq("course_id", course_id).execute().data or []
    existing_assign_ids = [a["assignment_id"] for a in existing_assign]
    incoming_assign_ids = [a.get("assignment_id") for a in assignments if a.get("assignment_id")]

    to_delete_assign = [aid for aid in existing_assign_ids if aid not in incoming_assign_ids]
    if to_delete_assign:
        supabase.table("assignments").delete().in_("assignment_id", to_delete_assign).execute()

    for a in assignments:
        assign_id = a.get("assignment_id") or generate_id()
        supabase.table("assignments").upsert({
            "assignment_id": assign_id,
            "course_id": course_id,
            "title": a["title"],
            "status": a["status"],
            "description": a.get("description"),
        }, on_conflict="assignment_id").execute()
