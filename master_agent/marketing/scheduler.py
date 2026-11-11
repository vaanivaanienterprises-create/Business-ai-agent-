import json
from datetime import datetime, date, time, timedelta

from master_agent.database import connect

PLATFORMS = [
    "Facebook",
    "Instagram",
    "YouTube",
    "Google Business Profile",
    "WhatsApp Business",
    "JustDial",
]

POST_TIMES = ["09:00", "11:00", "13:00", "15:00", "17:00"]
VIDEO_TIMES = ["10:00", "19:00"]


def build_daily_plan(target_date=None):
    now = datetime.now().astimezone()
    day = date.fromisoformat(target_date) if target_date else now.date()

    plan = []

    for platform in PLATFORMS:
        for content_type, slots in (
            ("post", POST_TIMES),
            ("video", VIDEO_TIMES),
        ):
            for slot in slots:
                hour, minute = map(int, slot.split(":"))
                scheduled = datetime.combine(
                    day, time(hour, minute), tzinfo=now.tzinfo
                )

                plan.append({
                    "platform": platform,
                    "content_type": content_type,
                    "scheduled_at": scheduled.isoformat(timespec="minutes"),
                })

    return sorted(plan, key=lambda x: x["scheduled_at"])


def create_daily_queue(target_date=None):
    """
    Empty planning slots are disabled.
    Only approved posts with real captions should enter the queue.
    """
    return {
        "success": True,
        "planned": 0,
        "created": 0,
        "skipped": 0,
        "message": "Empty queue slots disabled. Use approved caption posts only."
    }


if __name__ == "__main__":
    print("===== DAILY MARKETING PLAN =====")
    plan = build_daily_plan()

    for item in plan:
        print(
            item["platform"],
            item["content_type"],
            item["scheduled_at"],
        )

    print("Total planned:", len(plan))
