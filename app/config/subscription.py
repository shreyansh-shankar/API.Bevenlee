# Plan IDs
FREE = 0
PRO = 1
PREMIUM = 2

PLAN_LIMITS = {
    FREE: {
        "name": "Free",
        "max_courses": 3,
        "max_topics_per_course": 7
    },
    PRO: {
        "name": "Pro",
        "max_courses": 10,
        "max_topics_per_course": 12
    },
    PREMIUM: {
        "name": "Premium",
        "max_courses": -1,
        "max_topics_per_course": -1
    },
}

PLAN_PRICING = {
    FREE:    {"monthly": 0,   "yearly": 0},
    PRO:     {"monthly": 199, "yearly": 1999},
    PREMIUM: {"monthly": 399, "yearly": 3999},
}

PLAN_DURATIONS = {
    "monthly": 30,
    "yearly": 365,
}

# Creem product ID → internal plan_id + billing_cycle
CREEM_PRODUCT_MAP: dict[str, dict] = {}

def _register_direct(product_id: str, plan_id: int, billing_cycle: str):
    if product_id:
        CREEM_PRODUCT_MAP[product_id] = {
            "plan_id": plan_id,
            "billing_cycle": billing_cycle,
        }

def init_creem_product_map():
    from app.core.config import settings
    _register_direct(settings.CREEM_PRODUCT_ID_PRO_MONTHLY,     PRO,     "monthly")
    _register_direct(settings.CREEM_PRODUCT_ID_PRO_YEARLY,      PRO,     "yearly")
    _register_direct(settings.CREEM_PRODUCT_ID_PREMIUM_MONTHLY, PREMIUM, "monthly")
    _register_direct(settings.CREEM_PRODUCT_ID_PREMIUM_YEARLY,  PREMIUM, "yearly")

def get_creem_product_id(plan_id: int, billing_cycle: str) -> str:
    for product_id, meta in CREEM_PRODUCT_MAP.items():
        if meta["plan_id"] == plan_id and meta["billing_cycle"] == billing_cycle:
            return product_id
    raise ValueError(f"No Creem product found for plan={plan_id} cycle={billing_cycle}")