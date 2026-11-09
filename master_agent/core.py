from master_agent.database import init_db, connect
from master_agent.security.permissions import check_permission
from master_agent.providers.status import get_provider_status
from master_agent.apnacare_data import get_business_summary


def get_agent_status():
    init_db()

    with connect() as db:
        tasks = db.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]

        waiting = db.execute(
            "SELECT COUNT(*) FROM approval_requests WHERE status='waiting'"
        ).fetchone()[0]

    try:
        business = get_business_summary()
        business_status = "CONNECTED"
    except Exception as error:
        business = {"error": str(error)}
        business_status = "NOT CONNECTED"

    return {
        "agent": "ApnaCare AI Master Agent",
        "database": "READY",
        "tasks": tasks,
        "pending_approvals": waiting,
        "providers": get_provider_status(),
        "apnacare_status": business_status,
        "apnacare_business": business
    }


if __name__ == "__main__":
    print("===== ApnaCare AI Master Agent =====")

    for key, value in get_agent_status().items():
        print(f"{key}: {value}")

    print("===== Permission Test =====")
    print("Research:", check_permission("research"))
    print("Delete:", check_permission("delete_data"))
