from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.subscription_service import get_plan_limits
from app.services.add_course_service import get_user_plan

router = APIRouter()

class PlanRequest(BaseModel):
    user_id: str

@router.post("")
async def get_plan(payload: PlanRequest):
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