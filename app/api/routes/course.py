from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from app.services.course_service import create_course

router = APIRouter()

# Request model
class CreateCourseRequest(BaseModel):
    user_id: str
    title: str
    type: str
    purpose: Optional[str] = None
    status: Literal["planned", "active", "paused", "completed"]
    priority: Literal["low", "medium", "high"]


@router.post("")
async def create_course_route(payload: CreateCourseRequest):
    print("=" * 50)
    print("CREATE COURSE REQUEST")
    print("User ID:", payload.user_id)
    print("Title:", payload.title)
    print("Type:", payload.type)
    print("Status:", payload.status)
    print("Priority:", payload.priority)
    print("=" * 50)

    try:
        course = create_course(
            user_id=payload.user_id,
            title=payload.title,
            type=payload.type,
            purpose=payload.purpose,
            status=payload.status,
            priority=payload.priority,
        )

        return {
            "status": "ok",
            "course": course,
        }

    except Exception as e:
        print("❌ COURSE CREATE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to create course")
