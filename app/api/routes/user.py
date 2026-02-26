from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import verify_token
from pydantic import BaseModel
from app.services.subscription_service import get_plan_limits
from app.services.add_course_service import get_user_plan
from app.services.profile_service import (
    get_user_profile,
    update_user_profile,
)

router = APIRouter()

class PlanRequest(BaseModel):
    user_id: str


# =========================
# PLAN ROUTE
# =========================

@router.post("/plan")
async def get_plan(payload: PlanRequest, user=Depends(verify_token)):
    try:
        plan_id = get_user_plan(payload.user_id)
        limits = get_plan_limits(plan_id)

        return {
            "status": "ok",
            "plan": {
                "id": plan_id,
                "name": limits["name"],
                "limits": limits
            }
        }

    except Exception as e:
        print("❌ PLAN FETCH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch plan")

class ProfileUpdate(BaseModel):
    user_id: str
    full_name: str | None = None
    avatar_url: str | None = None


# =========================
# PROFILE ROUTES
# =========================

@router.get("/profile/{user_id}")
async def fetch_profile(user_id: str, user=Depends(verify_token)):
    try:
        profile = get_user_profile(user_id)

        return {
            "status": "ok",
            "profile": profile
        }

    except Exception as e:
        print("❌ PROFILE FETCH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

# =========================
# PROFILE ROUTES
# =========================

@router.put("/profile")
async def update_profile(payload: ProfileUpdate, user=Depends(verify_token)):
    try:
        updated = update_user_profile(
            payload.user_id,
            full_name=payload.full_name,
            avatar_url=payload.avatar_url,
        )

        return {
            "status": "ok",
            "profile": updated
        }

    except Exception as e:
        print("❌ PROFILE UPDATE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to update profile")