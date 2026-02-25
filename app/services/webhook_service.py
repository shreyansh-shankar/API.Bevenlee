import json
from datetime import datetime, timezone
from app.config.subscription import CREEM_PRODUCT_MAP, FREE
from app.services.billing_service import activate_user_plan, deactivate_user_plan
from app.core.supabase import supabase


def handle_webhook_event(event: dict):
    event_type = event.get("eventType")  # fixed: was "type"
    data = event.get("object", {})       # fixed: was "data"

    print(f"📩 Creem webhook received: {event_type}")

    if event_type in ("checkout.completed", "subscription.active", "subscription.paid"):
        _handle_grant_access(data)

    elif event_type == "subscription.update":
        _handle_grant_access(data)

    elif event_type in ("subscription.canceled", "subscription.expired", "subscription.paused"):
        _handle_revoke_access(data)

    elif event_type in ("subscription.unpaid", "subscription.past_due"):
        print(f"⚠️ Subscription payment issue: {data.get('id')}")

    else:
        print(f"ℹ️ Unhandled event type: {event_type}")


def _handle_grant_access(data: dict):
    metadata = data.get("metadata", {})
    user_id = metadata.get("userId")

    if not user_id:
        print("❌ No userId in webhook metadata")
        return

    # fixed: product_id is nested under data.product.id
    product_id = data.get("product", {}).get("id")
    plan_meta = CREEM_PRODUCT_MAP.get(product_id)

    if not plan_meta:
        print(f"❌ Unknown product_id in webhook: {product_id}")
        return

    plan_id = plan_meta["plan_id"]
    billing_cycle = plan_meta["billing_cycle"]

    # fixed: customer is nested under data.customer.id
    creem_customer_id = data.get("customer", {}).get("id", "")
    creem_subscription_id = data.get("id", "")

    # amount from last_transaction
    amount = data.get("last_transaction", {}).get("amount", 0)

    # expiry from current_period_end_date
    plan_expires_at = None
    period_end = data.get("current_period_end_date")
    if period_end:
        try:
            plan_expires_at = datetime.fromisoformat(period_end).astimezone(timezone.utc)
        except Exception:
            pass

    activate_user_plan(
        user_id=user_id,
        plan_id=plan_id,
        billing_cycle=billing_cycle,
        creem_customer_id=creem_customer_id,
        creem_subscription_id=creem_subscription_id,
        amount=amount,
        plan_expires_at=plan_expires_at,
    )

    print(f"✅ Access granted: user={user_id} plan={plan_id} cycle={billing_cycle}")


def _handle_revoke_access(data: dict):
    metadata = data.get("metadata", {})
    user_id = metadata.get("userId")

    if not user_id:
        # fallback: look up by creem_subscription_id
        sub_id = data.get("id")
        if sub_id:
            result = (
                supabase.table("users")
                .select("user_id")
                .eq("creem_subscription_id", sub_id)
                .single()
                .execute()
            )
            if result.data:
                user_id = result.data["user_id"]

    if not user_id:
        print("❌ Could not resolve user_id for revoke event")
        return

    deactivate_user_plan(user_id=user_id)
    print(f"🚫 Access revoked: user={user_id}")