import json
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timezone

from app.services.billing_service import get_user_subscription, get_payment_history
from app.services.creem_service import (
    create_checkout,
    cancel_subscription,
    upgrade_subscription,
    verify_webhook_signature,
)
from app.services.webhook_service import handle_webhook_event
from app.config.subscription import PLAN_LIMITS, FREE

router = APIRouter()


# --------------------------------------------------
# Create Checkout Session
# --------------------------------------------------
class CreateCheckoutRequest(BaseModel):
    user_id: str
    plan_id: int
    billing_cycle: str = "monthly"

@router.post("/create-checkout")
async def create_checkout_session(data: CreateCheckoutRequest):
    try:
        checkout_url = create_checkout(
            plan_id=data.plan_id,
            billing_cycle=data.billing_cycle,
            user_id=data.user_id,
        )
        return {"status": "ok", "checkout_url": checkout_url}
    except Exception as e:
        print("❌ CREATE CHECKOUT ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to create checkout")


# --------------------------------------------------
# Cancel Subscription
# --------------------------------------------------
class CancelRequest(BaseModel):
    user_id: str
    subscription_id: str

@router.post("/cancel")
async def cancel(data: CancelRequest):
    try:
        result = cancel_subscription(data.subscription_id)
        return {"status": "ok", "result": result}
    except Exception as e:
        print("❌ CANCEL ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


# --------------------------------------------------
# Upgrade / Downgrade Subscription
# --------------------------------------------------
class UpgradeRequest(BaseModel):
    user_id: str
    subscription_id: str
    plan_id: int
    billing_cycle: str = "monthly"
    update_behavior: str = "proration-charge-immediately"

@router.post("/upgrade")
async def upgrade(data: UpgradeRequest):
    try:
        result = upgrade_subscription(
            subscription_id=data.subscription_id,
            plan_id=data.plan_id,
            billing_cycle=data.billing_cycle,
            update_behavior=data.update_behavior,
        )
        return {"status": "ok", "result": result}
    except Exception as e:
        print("❌ UPGRADE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")


# --------------------------------------------------
# Webhook (Creem → your server)
# --------------------------------------------------
@router.post("/webhook")
async def creem_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("creem-signature", "")

    if not verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        event = json.loads(raw_body)
        handle_webhook_event(event)
    except Exception as e:
        print("❌ WEBHOOK PROCESSING ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")

    return {"received": True}


# --------------------------------------------------
# Get Current Subscription
# --------------------------------------------------
@router.get("/subscription/{user_id}")
async def get_subscription(user_id: str):
    try:
        subscription = get_user_subscription(user_id)
        return {"status": "ok", "subscription": subscription}
    except Exception as e:
        print("❌ SUBSCRIPTION FETCH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")


# --------------------------------------------------
# Payment History
# --------------------------------------------------
@router.get("/payments/{user_id}")
async def get_payments(user_id: str):
    try:
        payments = get_payment_history(user_id)
        return {"status": "ok", "payments": payments, "count": len(payments)}
    except Exception as e:
        print("❌ PAYMENT HISTORY ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch payments")