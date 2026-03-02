from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Literal, Optional
from app.core.auth import verify_token
from app.services.create_share_service import create_share
from app.services.get_share_preview_service import get_share_preview
from app.services.accept_share_service import (
    accept_share,
    ShareExpiredError,
    CourseLimitExceeded,
    TopicLimitExceeded,
    PlanUpgradeRequired,
)

router = APIRouter()

# ── Request models ──────────────────────────────────────────────────────────

class CreateShareRequest(BaseModel):
    user_id: str
    course_id: str
    expiry: Literal["never", "7d", "30d"]
    whiteboards: bool = False

class AcceptShareRequest(BaseModel):
    user_id: str


# ── Routes ──────────────────────────────────────────────────────────────────

@router.post("/create")
async def create_share_route(payload: CreateShareRequest, user=Depends(verify_token)):
    try:
        result = create_share(
            user_id=payload.user_id,
            course_id=payload.course_id,
            expiry=payload.expiry,
            whiteboards=payload.whiteboards,
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print("❌ CREATE SHARE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to create share link")


@router.get("/{token}")
async def get_share_preview_route(token: str):
    # No auth — this endpoint is intentionally public for the preview page
    try:
        preview = get_share_preview(token)
        if not preview:
            raise HTTPException(status_code=404, detail="Share link not found")
        return preview

    except HTTPException:
        raise
    except Exception as e:
        print("❌ GET SHARE PREVIEW ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch share preview")


@router.post("/{token}/accept")
async def accept_share_route(token: str, payload: AcceptShareRequest, user=Depends(verify_token)):
    try:
        result = accept_share(
            token=token,
            recipient_user_id=payload.user_id,
        )
        return result   # { "course_id": new_course_id }
    except PlanUpgradeRequired as e:        # ← now correctly inside the function
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
    except TopicLimitExceeded as e:
        raise HTTPException(
            status_code=403,
            detail={"error": str(e), "error_code": "TOPIC_LIMIT_EXCEEDED"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print("❌ ACCEPT SHARE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to accept share")