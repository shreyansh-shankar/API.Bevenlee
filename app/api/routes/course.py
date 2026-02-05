from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from app.services.add_course_service import create_course
from app.services.get_course_service import get_courses_by_user

router = APIRouter()

# Request model
class CreateCourseRequest(BaseModel):
    user_id: str
    title: str
    type: str
    purpose: Optional[str] = None
    status: Literal["planned", "active", "paused", "completed"]
    priority: Literal["low", "medium", "high"]
    projects_enabled: bool
    assignments_enabled: bool


@router.post("")
async def create_course_route(payload: CreateCourseRequest):
    print("=" * 50)
    print("CREATE COURSE REQUEST")
    print("User ID:", payload.user_id)
    print("Title:", payload.title)
    print("Type:", payload.type)
    print("Status:", payload.status)
    print("Priority:", payload.priority)
    print("Projects Enabled:", payload.projects_enabled)
    print("Assignments Enabled:", payload.assignments_enabled)
    print("=" * 50)

    try:
        course = create_course(
            user_id=payload.user_id,
            title=payload.title,
            type=payload.type,
            purpose=payload.purpose,
            status=payload.status,
            priority=payload.priority,
            projects_enabled=payload.projects_enabled,
            assignments_enabled=payload.assignments_enabled
        )

        return {
            "status": "ok",
            "course": course,
        }

    except Exception as e:
        print("❌ COURSE CREATE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to create course")

@router.get("/{user_id}")
async def get_courses_route(user_id: str):
    print("=" * 50)
    print("FETCH COURSES REQUEST")
    print("User ID:", user_id)
    print("=" * 50)

    try:
        courses = get_courses_by_user(user_id)

        return {
            "status": "ok",
            "courses": courses,
        }

    except Exception as e:
        print("❌ COURSE FETCH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch courses")
