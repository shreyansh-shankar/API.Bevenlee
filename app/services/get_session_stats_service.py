from app.core.supabase import supabase
from datetime import datetime, timedelta, timezone

def get_session_stats(user_id: str, topic_id: str) -> dict:
    result = supabase.table("study_sessions") \
        .select("session_id, topic_id, started_at, duration_minutes") \
        .eq("user_id", user_id) \
        .eq("topic_id", topic_id) \
        .order("started_at", desc=True) \
        .execute()

    sessions = result.data or []

    # Today's total minutes
    today = datetime.now(timezone.utc).date()
    today_minutes = sum(
        s["duration_minutes"] for s in sessions
    )

    # Streak — consecutive days going backwards from today
    days_with_sessions = set(
        datetime.fromisoformat(s["started_at"]).astimezone(timezone.utc).date()
        for s in sessions
    )
    streak = 0
    cursor = today
    while cursor in days_with_sessions:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "sessions": sessions,
        "today_minutes": today_minutes,
        "total_sessions": len(sessions),
        "streak_days": streak,
    }