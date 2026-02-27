from app.core.supabase import supabase

def delete_course(course_id: str):
    try:
        # 1. Get all topic IDs
        topics = (
            supabase.table("topics")
            .select("topic_id")
            .eq("course_id", course_id)
            .execute()
        ).data or []

        topic_ids = [t["topic_id"] for t in topics]

        # 2. Delete subtopics
        if topic_ids:
            supabase.table("subtopics").delete().in_("topic_id", topic_ids).execute()

        # 3. Delete topics
        supabase.table("topics").delete().eq("course_id", course_id).execute()

        # 4. Delete resources, projects, assignments
        supabase.table("resources").delete().eq("course_id", course_id).execute()
        supabase.table("projects").delete().eq("course_id", course_id).execute()
        supabase.table("assignments").delete().eq("course_id", course_id).execute()

        # 5. Delete course shares
        supabase.table("course_shares").delete().eq("course_id", course_id).execute()

        # 6. Finally delete the course
        supabase.table("courses").delete().eq("course_id", course_id).execute()

    except Exception as e:
        raise Exception(f"Failed to delete course: {e}")