"""
Metricool integration status for ApnaCare AI Master.
Configuration status only; no API calls or publishing.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)


def get_metricool_status():
    blog_id = os.getenv("METRICOOL_BLOG_ID", "").strip()
    user_id = os.getenv("METRICOOL_USER_ID", "").strip()
    timezone = os.getenv(
        "METRICOOL_TIMEZONE", "Asia/Calcutta"
    ).strip()

    configured = bool(blog_id and user_id)

    return {
        "brand_name": "ApnaCare",
        "blog_id_configured": bool(blog_id),
        "user_id_configured": bool(user_id),
        "configuration_status": (
            "configured" if configured else "incomplete"
        ),
        "timezone": timezone,
        "api_status": "not_verified",
        "publishing_enabled": False,
    }
