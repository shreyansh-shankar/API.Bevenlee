from app.core.supabase import supabase


def get_course_detail(course_id: str):
    # -------------------------------------------------
    # 1. Course (required)
    # -------------------------------------------------
    course_res = (
        supabase
        .table("courses")
        .select(
            "course_id, title, type, status, priority, purpose, projects_enabled, assignments_enabled"
        )
        .eq("course_id", course_id)
        .single()
        .execute()
    )

    course = course_res.data
    if not course:
        return None

    # -------------------------------------------------
    # 2. Topics
    # -------------------------------------------------
    topics_res = (
        supabase
        .table("topics")
        .select(
            "topic_id, title, status, position"
        )
        .eq("course_id", course_id)
        .order("position")
        .execute()
    )

    topics = topics_res.data or []

    # -------------------------------------------------
    # 3. Subtopics (ONLY if topics exist)
    # -------------------------------------------------
    subtopics = []
    if topics:
        topic_ids = [t["topic_id"] for t in topics]

        subtopics_res = (
            supabase
            .table("subtopics")
            .select(
                "subtopic_id, topic_id, title, is_completed, position"
            )
            .in_("topic_id", topic_ids)
            .order("position")
            .execute()
        )

        subtopics = subtopics_res.data or []

    # Attach subtopics → topics
    subtopics_by_topic = {}
    for sub in subtopics:
        subtopics_by_topic.setdefault(sub["topic_id"], []).append(sub)

    for topic in topics:
        topic["subtopics"] = subtopics_by_topic.get(topic["topic_id"], [])

    # -------------------------------------------------
    # 4. Resources
    # -------------------------------------------------
    resources = []

    if topics:
        topic_ids_str = ",".join([t["topic_id"] for t in topics])

        resources_res = (
            supabase
            .table("resources")
            .select(
                "resource_id, course_id, topic_id, title, url"
            )
            .or_(
                f"course_id.eq.{course_id},topic_id.in.({topic_ids_str})"
            )
            .execute()
        )
        resources = resources_res.data or []
    else:
        # Only course-level resources
        resources_res = (
            supabase
            .table("resources")
            .select(
                "resource_id, course_id, topic_id, title, url"
            )
            .eq("course_id", course_id)
            .execute()
        )
        resources = resources_res.data or []

    # -------------------------------------------------
    # 5. Projects (conditional)
    # -------------------------------------------------
    projects = []
    if course["projects_enabled"]:
        projects_res = (
            supabase
            .table("projects")
            .select(
                "project_id, course_id, title, status, description"
            )
            .eq("course_id", course_id)
            .order("created_at", desc=True)
            .execute()
        )
        projects = projects_res.data or []

    # -------------------------------------------------
    # 6. Assignments (conditional)
    # -------------------------------------------------
    assignments = []
    if course["assignments_enabled"]:
        assignments_res = (
            supabase
            .table("assignments")
            .select(
                "assignment_id, course_id, title, status, description"
            )
            .eq("course_id", course_id)
            .order("created_at", desc=True)
            .execute()
        )
        assignments = assignments_res.data or []

    # -------------------------------------------------
    # Final guaranteed-safe response
    # -------------------------------------------------
    return {
        "course": course,
        "topics": topics,
        "resources": resources,
        "projects": projects,
        "assignments": assignments,
    }
