from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, List
from app.services.add_course_service import create_course
from app.services.get_course_service import get_courses_by_user
from app.services.get_course_detail_service import get_course_detail
from app.services.save_course_service import save_course

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

# ------------------- Pydantic Models -------------------
class SubtopicPayload(BaseModel):
    subtopic_id: Optional[str]
    title: str
    is_completed: bool
    position: int

class TopicPayload(BaseModel):
    topic_id: Optional[str]
    title: str
    status: str
    position: int
    subtopics: List[SubtopicPayload] = []

class ResourcePayload(BaseModel):
    resource_id: Optional[str]
    topic_id: Optional[str] = None
    title: str
    url: str

class ProjectPayload(BaseModel):
    project_id: Optional[str]
    title: str
    status: str
    description: Optional[str] = None

class AssignmentPayload(BaseModel):
    assignment_id: Optional[str]
    title: str
    status: str
    description: Optional[str] = None

class CourseAggregatePayload(BaseModel):
    course_id: str
    course: dict
    topics: List[TopicPayload] = []
    resources: List[ResourcePayload] = []
    projects: List[ProjectPayload] = []
    assignments: List[AssignmentPayload] = []

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


@router.get("/detail/{course_id}")
async def get_course_detail_route(course_id: str):
    print("=" * 50)
    print("FETCH COURSE DETAIL REQUEST")
    print("Course ID:", course_id)
    print("=" * 50)

    try:
        course = get_course_detail(course_id)

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        return {
            "status": "ok",
            "course": course,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("❌ COURSE DETAIL ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch course detail")

@router.put("/save/{course_id}")
async def save_course_route(course_id: str, payload: CourseAggregatePayload):
    """
    Save/update full course aggregate (course, topics, subtopics, resources, projects, assignments)
    """
    try:
        save_course(course_id, payload.dict())
        return {"status": "ok"}
    except Exception as e:
        print("❌ SAVE COURSE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to save course")

