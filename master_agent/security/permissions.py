SAFE_ACTIONS = {
    "read_data",
    "view_dashboard",
    "generate_report",
    "draft_message",
    "research",
    "create_task",
}

APPROVAL_ACTIONS = {
    "send_message",
    "publish_post",
    "modify_website",
    "modify_code",
    "delete_data",
    "make_payment",
    "deploy",
    "submit_tender",
}


def check_permission(action):
    action = action.strip().lower()

    if action in SAFE_ACTIONS:
        return {
            "allowed": True,
            "approval_required": False,
            "message": "Safe action allowed."
        }

    return {
        "allowed": False,
        "approval_required": True,
        "message": "Approval required before this action."
    }


if __name__ == "__main__":
    for action in ["research", "send_message", "delete_data", "unknown_action"]:
        print(action, "=>", check_permission(action))
