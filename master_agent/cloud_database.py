import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent


def load_env():
    env = {}
    env_file = ROOT / ".env"

    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")

    env.update(os.environ)
    return env


def cloud_request(path, method="GET", payload=None):
    env = load_env()
    base_url = env.get("SUPABASE_URL", "").rstrip("/")
    secret = env.get("SUPABASE_SECRET_KEY", "")

    if not base_url.startswith("https://") or not secret.startswith("sb_secret_"):
        raise RuntimeError("Supabase configuration invalid")

    headers = {
        "apikey": secret,
        "Authorization": "Bearer " + secret,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = None if payload is None else json.dumps(payload).encode("utf-8")

    request = Request(
        base_url + "/rest/v1/" + path.lstrip("/"),
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return {
                "success": True,
                "status": response.status,
                "data": json.loads(body) if body else None,
            }
    except HTTPError as error:
        detail = error.read(500).decode("utf-8", "replace")
        raise RuntimeError(f"Supabase HTTP {error.code}: {detail}") from None
    except URLError as error:
        raise RuntimeError(f"Supabase connection failed: {error}") from None


def get_cloud_settings():
    result = cloud_request(
        "settings?select=key,value"
        "&key=in.(marketing_mode,marketing_paused,marketing_publishing_enabled)"
    )

    values = {row["key"]: row["value"] for row in result["data"] or []}

    return {
        "mode": values.get("marketing_mode", "manual"),
        "paused": values.get("marketing_paused", "1") == "1",
        "publishing_enabled": False,
        "status": "PAUSED" if values.get("marketing_paused", "1") == "1" else "READY",
    }


if __name__ == "__main__":
    print("Checking Supabase connection...")
    settings = get_cloud_settings()
    print("CLOUD CONNECTION SUCCESS")
    print("Marketing mode:", settings["mode"])
    print("Paused:", settings["paused"])
    print("Publishing enabled:", settings["publishing_enabled"])
