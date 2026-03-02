from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Literal
from app.core.auth import verify_token
from app.services.create_roadmap_share_service import create_roadmap_share
from app.services.get_roadmap_share_preview_service import get_roadmap_share_preview
from app.services.accept_roadmap_share_service import (
    accept_roadmap_share,
    ShareExpiredError,
    CourseLimitExceeded,
    PlanUpgradeRequired,
)

router = APIRouter()

class CreateRoadmapShareRequest(BaseModel):
    user_id: str
    roadmap_id: str
    expiry: Literal["never", "7d", "30d"]
    whiteboards: bool = False

class AcceptRoadmapShareRequest(BaseModel):
    user_id: str


@router.post("/create")
async def create_roadmap_share_route(
    payload: CreateRoadmapShareRequest,
    user=Depends(verify_token)
):
    try:
        result = create_roadmap_share(
            user_id=payload.user_id,
            roadmap_id=payload.roadmap_id,
            expiry=payload.expiry,
            whiteboards=payload.whiteboards,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print("❌ CREATE ROADMAP SHARE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to create share link")


@router.get("/{token}")
async def get_roadmap_share_preview_route(token: str):
    try:
        preview = get_roadmap_share_preview(token)
        if not preview:
            raise HTTPException(status_code=404, detail="Share link not found")
        return preview
    except HTTPException:
        raise
    except Exception as e:
        print("❌ GET ROADMAP SHARE PREVIEW ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch share preview")


@router.post("/{token}/accept")
async def accept_roadmap_share_route(
    token: str,
    payload: AcceptRoadmapShareRequest,
    user=Depends(verify_token)
):
    try:
        result = accept_roadmap_share(
            token=token,
            recipient_user_id=payload.user_id,
        )
        return result  # { "roadmap_id": new_roadmap_id }
    except PlanUpgradeRequired as e:
        raise HTTPException(
            status_code=403,
            detail={"error": str(e), "error_code": "PLAN_UPGRADE_REQUIRED"},
        )
    except ShareExpiredError as e:
        raise HTTPException(
            status_code=410,
            detail={"error": str(e), "error_code": "SHARE_EXPIRED"},
        )
    except CourseLimitExceeded as e:
        raise HTTPException(
            status_code=403,
            detail={"error": str(e), "error_code": "COURSE_LIMIT_EXCEEDED"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print("❌ ACCEPT ROADMAP SHARE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to accept roadmap share")