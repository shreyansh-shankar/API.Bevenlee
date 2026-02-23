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
        "max_courses": -1,  # unlimited
        "max_topics_per_course": -1
    },
}