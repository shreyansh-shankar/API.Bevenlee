from fastapi import HTTPException
from app.config.subscription import PLAN_LIMITS, FREE

def enforce_topic_limit(plan_id: int, topics: list):
    limits = PLAN_LIMITS.get(plan_id, PLAN_LIMITS[FREE])
    max_topics = limits.get("max_topics_per_course", -1)

    # unlimited
    if max_topics == -1:
        return

    topic_count = len(topics)

    if topic_count > max_topics:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TOPIC_LIMIT_EXCEEDED",
                "message": f"You can only create {max_topics} topics on the {limits['name']} plan.",
                "limit": max_topics,
                "current": topic_count,
            },
        )