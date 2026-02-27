from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.auth import verify_token
from app.services.save_session_service import save_session
from app.services.get_session_stats_service import get_session_stats

router = APIRouter()

class SaveSessionRequest(BaseModel):
    user_id: str
    topic_id: str
    started_at: str        # ISO 8601 string
    duration_minutes: int

@router.post("")
async def save_session_route(payload: SaveSessionRequest, user=Depends(verify_token)):
    try:
        if payload.duration_minutes < 1:
            raise HTTPException(status_code=400, detail="duration_minutes must be at least 1")

        result = save_session(
            user_id=payload.user_id,
            topic_id=payload.topic_id,
            started_at=payload.started_at,
            duration_minutes=payload.duration_minutes,
        )
        return {"success": True, "session_id": result["session_id"]}

    except HTTPException:
        raise
    except Exception as e:
        print("❌ SAVE SESSION ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to save session")

@router.get("/stats")
async def get_session_stats_route(topic_id: str, user_id: str, user=Depends(verify_token)):
    try:
        stats = get_session_stats(user_id=user_id, topic_id=topic_id)
        return stats

    except Exception as e:
        print("❌ GET SESSION STATS ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch session stats")