from app.config.subscription import PLAN_LIMITS, FREE

def get_plan_limits(plan_id: int):
    return PLAN_LIMITS.get(plan_id, PLAN_LIMITS[FREE])