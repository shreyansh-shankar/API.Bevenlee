from datetime import datetime, timedelta, timezone
from app.core.supabase import supabase
import math
from app.config.subscription import (
    PLAN_LIMITS,
    FREE,
)
from app.services.subscription_service import ( get_plan_price, get_plan_duration_days )

# -------------------------------------------------
# Change User Plan
# -------------------------------------------------

def change_user_plan(*, user_id: str, plan_id: int, billing_cycle: str = "monthly"):
    if plan_id not in PLAN_LIMITS:
        raise Exception("Invalid plan")

    # -----------------------------
    # 0️⃣ Determine plan details
    # -----------------------------
    if plan_id == FREE:
        # FREE plan → no payment, no expiry
        plan_start = None
        plan_expiry = None
        amount = 0
    else:
        # Paid plan
        amount = get_plan_price(plan_id, billing_cycle)
        duration_days = get_plan_duration_days(billing_cycle)
        plan_start = datetime.utcnow()
        plan_expiry = plan_start + timedelta(days=duration_days)

    # -----------------------------
    # 1️⃣ Insert payment record (skip for FREE)
    # -----------------------------
    payment_res = None
    if plan_id != FREE:
        payment_res = (
            supabase
            .table("payments")
            .insert({
                "user_id": user_id,
                "plan_id": plan_id,
                "amount": amount,
                "status": "success",
                "currency": "USD",
                "payment_provider": "mock",
                "payment_provider_id": f"mock_{datetime.utcnow().timestamp()}",
                "created_at": datetime.utcnow().isoformat(),
            })
            .execute()
        )

        if payment_res.data is None:
            raise Exception("Payment insert failed")

    # -----------------------------
    # 2️⃣ Update user subscription
    # -----------------------------
    update_res = (
        supabase
        .table("users")
        .update({
            "subscribed_plan": plan_id,
            "plan_started_at": plan_start.isoformat() if plan_start else None,
            "plan_expires_at": plan_expiry.isoformat() if plan_expiry else None,
        })
        .eq("user_id", user_id)
        .execute()
    )

    if update_res.data is None:
        raise Exception("User plan update failed")

    # -----------------------------
    # 3️⃣ Return response
    # -----------------------------
    return {
        "plan_id": plan_id,
        "plan_name": PLAN_LIMITS[plan_id]["name"],
        "amount_charged": amount,
        "billing_cycle": billing_cycle,
        "plan_started_at": plan_start,
        "plan_expires_at": plan_expiry,
    }

# -------------------------------------------------
# Get Current Subscription
# -------------------------------------------------

def get_user_subscription(user_id: str):
    response = (
        supabase
        .table("users")
        .select("subscribed_plan, plan_started_at, plan_expires_at")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        return {
            "plan_id": FREE,
            "plan_name": PLAN_LIMITS[FREE]["name"],
            "plan_started_at": None,
            "plan_expires_at": None,
            "is_active": True,
            "days_remaining": None,
        }

    plan_id = response.data["subscribed_plan"]
    started_at = response.data.get("plan_started_at")
    expires_at = response.data.get("plan_expires_at")

    now = datetime.now(timezone.utc)

    # -----------------------------------
    # auto downgrade if expired
    # -----------------------------------
    if expires_at:
        expiry_dt = datetime.fromisoformat(expires_at).astimezone(timezone.utc)

        if expiry_dt < now:
            # downgrade to FREE
            supabase.table("users").update({
                "subscribed_plan": FREE,
                "plan_started_at": None,
                "plan_expires_at": None,
            }).eq("user_id", user_id).execute()

            return {
                "plan_id": FREE,
                "plan_name": PLAN_LIMITS[FREE]["name"],
                "plan_started_at": None,
                "plan_expires_at": None,
                "is_active": True,
                "days_remaining": None,
            }

        # still active → calculate remaining days
        remaining_days = math.ceil((expiry_dt - now).total_seconds() / 86400)
    else:
        remaining_days = None

    return {
        "plan_id": plan_id,
        "plan_name": PLAN_LIMITS[plan_id]["name"],
        "plan_started_at": started_at,
        "plan_expires_at": expires_at,
        "is_active": True,
        "days_remaining": remaining_days,
    }


# -------------------------------------------------
# Payment History
# -------------------------------------------------

def get_payment_history(user_id: str):
    response = (
        supabase
        .table("payments")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []