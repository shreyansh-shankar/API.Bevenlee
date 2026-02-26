from datetime import datetime, timezone
from app.config.subscription import CREEM_PRODUCT_MAP
from app.services.billing_service import activate_user_plan, deactivate_user_plan, mark_subscription_cancelled
from app.core.supabase import supabase


def handle_webhook_event(event: dict):
    event_type = event.get("eventType")
    data = event.get("object", {})
    print(f"📩 Creem webhook received: {event_type}")

    if event_type in ("checkout.completed", "subscription.active", "subscription.paid"):
        _handle_grant_access(data)

    elif event_type == "subscription.update":
        _handle_grant_access(data)

    elif event_type == "subscription.canceled":
        _handle_soft_cancel(data)

    elif event_type in ("subscription.expired", "subscription.unpaid", "subscription.past_due"):
        _handle_revoke_access(data)

    else:
        print(f"ℹ️ Unhandled event type: {event_type}")


def _resolve_user_id(data: dict) -> str | None:
    """Try metadata first, then fall back to DB lookup by subscription ID."""
    user_id = data.get("metadata", {}).get("userId")
    if user_id:
        return user_id

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
            return result.data["user_id"]

    return None


def _handle_grant_access(data: dict):
    user_id = _resolve_user_id(data)  # ← now uses the shared helper
    if not user_id:
        print("❌ No userId in webhook metadata")
        return

    product_id = data.get("product", {}).get("id")
    plan_meta = CREEM_PRODUCT_MAP.get(product_id)
    if not plan_meta:
        print(f"❌ Unknown product_id in webhook: {product_id}")
        return

    plan_id = plan_meta["plan_id"]
    billing_cycle = plan_meta["billing_cycle"]
    creem_customer_id = data.get("customer", {}).get("id", "")
    creem_subscription_id = data.get("id", "")
    amount = data.get("last_transaction", {}).get("amount", 0)

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
        status="active",  # ← was missing
    )
    print(f"✅ Access granted: user={user_id} plan={plan_id} cycle={billing_cycle}")


def _handle_soft_cancel(data: dict):
    """Cancelled but valid until period end — status → cancelled, access preserved."""
    user_id = _resolve_user_id(data)
    if not user_id:
        print("❌ Could not resolve user_id for soft cancel")
        return

    plan_expires_at = None
    period_end = data.get("current_period_end_date")
    if period_end:
        try:
            plan_expires_at = datetime.fromisoformat(period_end).astimezone(timezone.utc)
        except Exception:
            pass

    mark_subscription_cancelled(user_id=user_id, plan_expires_at=plan_expires_at)
    print(f"🟡 Subscription cancelled (access until {period_end}): user={user_id}")


def _handle_revoke_access(data: dict):
    """Hard revoke — expired, unpaid, or past due."""
    user_id = _resolve_user_id(data)  # ← now uses the shared helper
    if not user_id:
        print("❌ Could not resolve user_id for revoke event")
        return

    deactivate_user_plan(user_id=user_id)
    print(f"🚫 Access revoked: user={user_id}")