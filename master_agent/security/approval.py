from master_agent.database import connect, init_db


def review_approval(request_id, decision):
    decision = decision.strip().lower()

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

        db.execute(
            "UPDATE approval_requests SET status = ? WHERE id = ?",
            (new_status, request_id)
        )

        db.execute(
            "INSERT INTO activity_logs (action, details) VALUES (?, ?)",
            ("approval_review", f"Request {request_id}: {new_status}")
        )

    return {
        "success": True,
        "request_id": request_id,
        "status": new_status
    }


if __name__ == "__main__":
    init_db()
    print("Approval Manager READY")
    print("No action is executed by this test.")
