import json
from master_agent.database import connect, init_db


def review_approval(request_id, decision):
    decision = str(decision).strip().lower()

    if decision not in ("approve", "reject"):
        return {"success": False, "message": "Invalid decision."}

    new_status = "approved" if decision == "approve" else "rejected"

    with connect() as db:
        request = db.execute(
            "SELECT * FROM approval_requests WHERE id = ?",
            (request_id,)
        ).fetchone()

        if request is None:
            return {"success": False, "message": "Approval request not found."}

        if request["status"] != "waiting":
            return {"success": False, "message": "Request already reviewed."}

        queued = 0

        if decision == "approve" and request["action"] == "marketing_draft_review":
            try:
                details = json.loads(request["details"])
            except (ValueError, TypeError):
                return {"success": False, "message": "Invalid marketing draft data."}

            if not isinstance(details, dict):
                return {"success": False, "message": "Invalid marketing draft data."}

            captions = {
                "Facebook": details.get("facebook_draft"),
                "Instagram": details.get("instagram_draft"),
            }

            if not all(isinstance(value, str) and value.strip()
                       for value in captions.values()):
                return {"success": False, "message": "Marketing draft is incomplete."}

            for platform, caption in captions.items():
                db.execute("""
                    INSERT INTO marketing_posts
                    (platform, content_type, caption, scheduled_at, status)
                    VALUES (?, 'post', ?, NULL, 'planned')
                """, (platform, caption.strip()))
                queued += 1

        db.execute(
            "UPDATE approval_requests SET status = ? WHERE id = ? AND status = 'waiting'",
            (new_status, request_id)
        )

        db.execute(
            "INSERT INTO activity_logs (action, details) VALUES (?, ?)",
            (
                "approval_review",
                f"Request {request_id}: {new_status}; Queue items: {queued}"
            )
        )

        return {
            "success": True,
            "request_id": request_id,
            "status": new_status,
            "queued": queued,
            "message": f"Approval completed. {queued} items added to the internal queue. Not published."
        }


if __name__ == "__main__":
    init_db()
    print("Approval Manager READY")
    print("External publishing is not performed.")
