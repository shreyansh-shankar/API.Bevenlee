from app.config.subscription import PLAN_LIMITS, FREE, PLAN_PRICING, PLAN_DURATIONS

def get_plan_limits(plan_id: int):
    return PLAN_LIMITS.get(plan_id, PLAN_LIMITS[FREE])

def get_plan_name(plan_id: int) -> str:
    return PLAN_LIMITS.get(plan_id, PLAN_LIMITS[FREE])["name"]

def get_plan_price(plan_id: int, billing_cycle: str) -> int:
    if plan_id not in PLAN_PRICING:
        return 0

    if billing_cycle not in PLAN_PRICING[plan_id]:
        raise ValueError("Invalid billing cycle")

    return PLAN_PRICING[plan_id][billing_cycle]

def get_plan_duration_days(billing_cycle: str) -> int:
    if billing_cycle not in PLAN_DURATIONS:
        raise ValueError("Invalid billing cycle")

    return PLAN_DURATIONS[billing_cycle]