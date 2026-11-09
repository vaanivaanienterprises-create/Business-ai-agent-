from master_agent.database import connect, init_db
from master_agent.security.permissions import check_permission


def submit_action(action, details=""):
    permission = check_permission(action)

    with connect() as db:
        if permission["approval_required"]:
            db.execute(
                "INSERT INTO approval_requests (action, details) VALUES (?, ?)",
                (action, details)
            )
            status = "approval_pending"
        else:
            status = "allowed"

        db.execute(
            "INSERT INTO activity_logs (action, details) VALUES (?, ?)",
            (action, f"{status}: {details}")
        )

    return {
        "action": action,
        "status": status,
        "message": permission["message"]
    }


def create_task(title, description="", task_type="general"):
    with connect() as db:
        cursor = db.execute(
            """INSERT INTO tasks (title, description, task_type)
               VALUES (?, ?, ?)""",
            (title, description, task_type)
        )
        return cursor.lastrowid


if __name__ == "__main__":
    init_db()

    task_id = create_task(
        "ApnaCare AI Master Agent setup",
        "Day 1 core setup task"
    )
    print("Task created:", task_id)

    print(submit_action("research", "ApnaCare market research"))
    print(submit_action("publish_post", "Marketing post publication test"))
