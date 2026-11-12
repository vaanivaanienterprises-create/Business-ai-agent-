from datetime import datetime, timezone

from master_agent.cloud_database import (
    cloud_request,
    get_cloud_settings,
)


def run_worker():
    print("===== APNACARE CLOUD WORKER =====")

    settings = get_cloud_settings()

    print("Marketing Mode:", settings["mode"])
    print("Marketing Paused:", settings["paused"])
    print("Publishing Enabled:", settings["publishing_enabled"])

    if settings["paused"]:
        print("WORKER STATUS: PAUSED")
        print("No jobs processed.")
        return

    now = datetime.now(timezone.utc).isoformat()

    path = (
        "marketing_jobs?select=id,job_type,run_at,status,"
        "attempts,payload_json"
        "&status=eq.pending"
        f"&run_at=lte.{now}"
        "&order=run_at.asc"
        "&limit=50"
    )

    result = cloud_request(path)
    jobs = result.get("data") or []

    print("Due Jobs Found:", len(jobs))

    for job in jobs:
        print(
            "Job:",
            job["id"],
            "| Type:",
            job["job_type"],
            "| Status:",
            job["status"],
        )

    print("DRY RUN COMPLETE")
    print("No jobs updated. Nothing published.")


if __name__ == "__main__":
    try:
        run_worker()
    except Exception as error:
        print("WORKER ERROR:", type(error).__name__, str(error))
        raise
