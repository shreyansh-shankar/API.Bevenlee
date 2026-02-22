# Plan IDs
FREE = 0
PRO = 1
PREMIUM = 2

PLAN_LIMITS = {
    FREE: {
        "name": "Free",
        "max_courses": 4,
    },
    PRO: {
        "name": "Pro",
        "max_courses": 12,
    },
    PREMIUM: {
        "name": "Premium",
        "max_courses": -1,  # unlimited
    },
}