from fastapi import APIRouter, HTTPException
from app.services.billing_service import change_user_plan, get_payment_history, get_user_subscription
from pydantic import BaseModel
from app.config.subscription import PLAN_LIMITS
from datetime import datetime, timezone

router = APIRouter()

class ChangePlanRequest(BaseModel):
    user_id: str
    plan_id: int
    billing_cycle: str = "monthly"
# -----------------------------
# Change Plan
# -----------------------------
@router.post("/change-plan")
async def change_plan(data: ChangePlanRequest):
    try:
        result = change_user_plan(
            user_id=data.user_id,
            plan_id=data.plan_id,
            billing_cycle=data.billing_cycle,
        )

        return {
            "status": "ok",
            "message": "Plan updated successfully",
            "plan": result,
        }

    except Exception as e:
        print("❌ CHANGE PLAN ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to update plan")

# -----------------------------
# Get Current Subscription
# -----------------------------
@router.get("/subscription/{user_id}")
async def get_subscription(user_id: str):
    try:
        subscription = get_user_subscription(user_id)

        expires_at = subscription.get("plan_expires_at")

        is_active = True
        days_remaining = None

        if expires_at:
            expiry_date = datetime.fromisoformat(expires_at)
            now = datetime.now(timezone.utc)

            if expiry_date < now:
                is_active = False
            else:
                days_remaining = (expiry_date - now).days

        return {
            "status": "ok",
            "subscription": {
                **subscription,
                "is_active": is_active,
                "days_remaining": days_remaining,
            },
        }

    except Exception as e:
        print("❌ SUBSCRIPTION FETCH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")


# -----------------------------
# Get Payment History
# -----------------------------
@router.get("/payments/{user_id}")
async def get_payments(user_id: str):
    try:
        payments = get_payment_history(user_id)

        return {
            "status": "ok",
            "payments": payments,
            "count": len(payments),
        }

    except Exception as e:
        print("❌ PAYMENT HISTORY ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch payments")