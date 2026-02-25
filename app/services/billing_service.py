import math
from datetime import datetime, timezone
from app.core.supabase import supabase
from app.config.subscription import PLAN_LIMITS, FREE, CREEM_PRODUCT_MAP


# --------------------------------------------------
# Called by webhook: grant access
# --------------------------------------------------
def activate_user_plan(
    *,
    user_id: str,
    plan_id: int,
    billing_cycle: str,
    creem_customer_id: str,
    creem_subscription_id: str,
    amount: int,
    plan_expires_at: datetime | None,
):
    now = datetime.now(timezone.utc)

    # Update user row
    supabase.table("users").update({
        "subscribed_plan": plan_id,
        "plan_started_at": now.isoformat(),
        "plan_expires_at": plan_expires_at.isoformat() if plan_expires_at else None,
        "creem_customer_id": creem_customer_id,
        "creem_subscription_id": creem_subscription_id,
    }).eq("user_id", user_id).execute()

    # Insert payment record
    supabase.table("payments").insert({
        "user_id": user_id,
        "plan_id": plan_id,
        "amount": amount,
        "status": "success",
        "currency": "USD",
        "payment_provider": "creem",
        "payment_provider_id": creem_subscription_id,
        "created_at": now.isoformat(),
    }).execute()


# --------------------------------------------------
# Called by webhook: revoke access
# --------------------------------------------------
def deactivate_user_plan(*, user_id: str):
    supabase.table("users").update({
        "subscribed_plan": FREE,
        "plan_started_at": None,
        "plan_expires_at": None,
        "creem_subscription_id": None,
    }).eq("user_id", user_id).execute()


# --------------------------------------------------
# Get current subscription for a user
# --------------------------------------------------
def get_user_subscription(user_id: str) -> dict:
    response = (
        supabase.table("users")
        .select("subscribed_plan, plan_started_at, plan_expires_at, creem_customer_id, creem_subscription_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not response.data:
        return _free_plan_response()

    data = response.data
    plan_id = data["subscribed_plan"]
    expires_at = data.get("plan_expires_at")
    now = datetime.now(timezone.utc)

    # Auto-downgrade if expired
    if expires_at:
        expiry_dt = datetime.fromisoformat(expires_at).astimezone(timezone.utc)
        if expiry_dt < now:
            deactivate_user_plan(user_id=user_id)
            return _free_plan_response()
        remaining_days = math.ceil((expiry_dt - now).total_seconds() / 86400)
    else:
        remaining_days = None

    return {
        "plan_id": plan_id,
        "plan_name": PLAN_LIMITS[plan_id]["name"],
        "plan_started_at": data.get("plan_started_at"),
        "plan_expires_at": expires_at,
        "creem_customer_id": data.get("creem_customer_id"),
        "creem_subscription_id": data.get("creem_subscription_id"),
        "is_active": True,
        "days_remaining": remaining_days,
    }


def _free_plan_response() -> dict:
    return {
        "plan_id": FREE,
        "plan_name": PLAN_LIMITS[FREE]["name"],
        "plan_started_at": None,
        "plan_expires_at": None,
        "creem_customer_id": None,
        "creem_subscription_id": None,
        "is_active": True,
        "days_remaining": None,
    }


# --------------------------------------------------
# Payment history
# --------------------------------------------------
def get_payment_history(user_id: str) -> list:
    response = (
        supabase.table("payments")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []