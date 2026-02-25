import os
import hmac
import hashlib
import httpx
from app.config.subscription import get_creem_product_id
from app.core.config import settings

CREEM_API_KEY = settings.CREEM_API_KEY
CREEM_WEBHOOK_SECRET = settings.CREEM_WEBHOOK_SECRET
CREEM_API_BASE = settings.CREEM_API_BASE
APP_URL = settings.APP_URL

HEADERS = {
    "x-api-key": CREEM_API_KEY,
    "Content-Type": "application/json",
}

# --------------------------------------------------
# Create a Creem checkout session
# --------------------------------------------------
def create_checkout(plan_id: int, billing_cycle: str, user_id: str) -> str:
    product_id = get_creem_product_id(plan_id, billing_cycle)

    payload = {
        "product_id": product_id,
        "success_url": f"{APP_URL}/billing/success",
        "metadata": {
            "userId": user_id,
            "planId": str(plan_id),
            "billingCycle": billing_cycle,
        },
    }

    response = httpx.post(
        f"{CREEM_API_BASE}/v1/checkouts",
        json=payload,
        headers=HEADERS,
        timeout=10,
    )

    response.raise_for_status()
    data = response.json()
    return data["checkout_url"]


# --------------------------------------------------
# Cancel a Creem subscription
# --------------------------------------------------
def cancel_subscription(subscription_id: str) -> dict:
    response = httpx.post(
        f"{CREEM_API_BASE}/v1/subscriptions/{subscription_id}/cancel",
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


# --------------------------------------------------
# Upgrade / downgrade a Creem subscription
# --------------------------------------------------
def upgrade_subscription(
    subscription_id: str,
    plan_id: int,
    billing_cycle: str,
    update_behavior: str = "proration-charge-immediately",
) -> dict:
    product_id = get_creem_product_id(plan_id, billing_cycle)

    response = httpx.post(
        f"{CREEM_API_BASE}/v1/subscriptions/{subscription_id}/upgrade",
        json={
            "productId": product_id,
            "updateBehavior": update_behavior,
        },
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


# --------------------------------------------------
# Verify incoming webhook signature
# --------------------------------------------------
def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    mac = hmac.new(
        CREEM_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    )
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature)