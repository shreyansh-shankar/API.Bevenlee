from app.core.supabase import supabase
from datetime import datetime
from app.services.subscription_service import get_plan_limits
from app.core.exceptions import PlanLimitExceeded

def get_user_plan(user_id: str) -> int:
    response = (
        supabase
        .table("users")
        .select("subscribed_plan")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        return 0

    return response.data["subscribed_plan"]


def get_course_count(user_id: str) -> int:
    response = (
        supabase
        .table("courses")
        .select("course_id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )

    return response.count or 0

def create_course(
    *,
    user_id: str,
    title: str,
    type: str,
    purpose: str | None,
    status: str,
    priority: str,
    projects_enabled: bool,
    assignments_enabled: bool,
):
    # ✅ get user plan
    plan_id = get_user_plan(user_id)

    # ✅ get plan limits
    limits = get_plan_limits(plan_id)

    # ✅ count courses
    current_count = get_course_count(user_id)

    max_courses = limits["max_courses"]

    if max_courses != -1 and current_count >= max_courses:
        raise PlanLimitExceeded(
            f"You have reached the limit of {max_courses} courses for the {limits['name']} plan."
        )

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
                "projects_enabled": projects_enabled,
                "assignments_enabled": assignments_enabled,
                "created_at": datetime.utcnow().isoformat(),
            })
            .execute()
        )

        return response.data

    except Exception as e:
        # ONLY database errors land here
        raise Exception(str(e))
