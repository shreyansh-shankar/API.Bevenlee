from app.core.supabase import supabase

def get_roadmap_detail(roadmap_id: str):
    # 1. Fetch roadmap
    roadmap_res = (
        supabase
        .table("roadmaps")
        .select("roadmap_id, user_id, title, description, course_ids, created_at")
        .eq("roadmap_id", roadmap_id)
        .single()
        .execute()
    )

    roadmap = roadmap_res.data
    if not roadmap:
        return None

    course_ids: list = roadmap.get("course_ids") or []

    if not course_ids:
        return {
            "roadmap": roadmap,
            "courses": [],
        }

    # 2. Fetch all courses in one query
    courses_res = (
        supabase
        .table("courses")
        .select("course_id, title, type, status, priority, purpose, projects_enabled, assignments_enabled")
        .in_("course_id", course_ids)
        .execute()
    )

    courses_map = {c["course_id"]: c for c in (courses_res.data or [])}

    # 3. Fetch all topics for these courses in one query
    topics_res = (
        supabase
        .table("topics")
        .select("topic_id, course_id, title, status, position")
        .in_("course_id", course_ids)
        .order("position")
        .execute()
    )

    topics_by_course: dict = {}
    for topic in (topics_res.data or []):
        topics_by_course.setdefault(topic["course_id"], []).append(topic)

    # 4. Build ordered course list (preserve course_ids order)
    ordered_courses = []
    for cid in course_ids:
        course = courses_map.get(cid)
        if not course:
            continue  # course was deleted, skip

        topics = topics_by_course.get(cid, [])
        total = len(topics)
        completed = sum(1 for t in topics if t.get("status") == "completed")

        ordered_courses.append({
            **course,
            "topics": topics,
            "total_topics": total,
            "completed_topics": completed,
        })

    return {
        "roadmap": roadmap,
        "courses": ordered_courses,
    }