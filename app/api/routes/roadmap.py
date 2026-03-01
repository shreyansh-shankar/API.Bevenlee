from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import verify_token
from pydantic import BaseModel
from typing import Optional, List

from app.services.create_roadmap_service import create_roadmap
from app.services.get_roadmaps_service import get_roadmaps_by_user
from app.services.get_roadmap_detail_service import get_roadmap_detail
from app.services.save_roadmap_service import save_roadmap
from app.services.delete_roadmap_service import delete_roadmap

router = APIRouter()


# ─────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────

class CreateRoadmapRequest(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None


class SaveRoadmapRequest(BaseModel):
    title: str
    description: Optional[str] = None
    course_ids: List[str] = []


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.post("")
async def create_roadmap_route(payload: CreateRoadmapRequest, user=Depends(verify_token)):
    try:
        roadmap = create_roadmap(
            user_id=payload.user_id,
            title=payload.title,
            description=payload.description,
        )
        return {"status": "ok", "roadmap": roadmap}
    except Exception as e:
        print("❌ ROADMAP CREATE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to create roadmap")


@router.get("/user/{user_id}")
async def get_roadmaps_route(user_id: str, user=Depends(verify_token)):
    try:
        roadmaps = get_roadmaps_by_user(user_id)
        return {"status": "ok", "roadmaps": roadmaps}
    except Exception as e:
        print("❌ ROADMAP FETCH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch roadmaps")


@router.get("/detail/{roadmap_id}")
async def get_roadmap_detail_route(roadmap_id: str, user=Depends(verify_token)):
    try:
        roadmap = get_roadmap_detail(roadmap_id)
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        return {"status": "ok", "roadmap": roadmap}
    except HTTPException:
        raise
    except Exception as e:
        print("❌ ROADMAP DETAIL ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch roadmap detail")


@router.put("/save/{roadmap_id}")
async def save_roadmap_route(roadmap_id: str, payload: SaveRoadmapRequest, user=Depends(verify_token)):
    try:
        updated = save_roadmap(
            roadmap_id=roadmap_id,
            title=payload.title,
            description=payload.description,
            course_ids=payload.course_ids,
        )
        return {"status": "ok", "roadmap": updated}
    except Exception as e:
        print("❌ ROADMAP SAVE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to save roadmap")


@router.delete("/{roadmap_id}")
async def delete_roadmap_route(roadmap_id: str, user=Depends(verify_token)):
    try:
        delete_roadmap(roadmap_id)
        return {"status": "ok", "message": "Roadmap deleted successfully"}
    except Exception as e:
        print("❌ ROADMAP DELETE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to delete roadmap")