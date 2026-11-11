from master_agent.database import connect

DEFAULTS = {
    "marketing_mode": "manual",
    "marketing_paused": "1",
    "marketing_publishing_enabled": "0",
}


def initialize_marketing_control():
    with connect() as db:
        for key, value in DEFAULTS.items():
            db.execute("""
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
            """, (key, value))


def get_marketing_control():
    initialize_marketing_control()

    with connect() as db:
        rows = db.execute("""
            SELECT key, value
            FROM settings
            WHERE key IN (
                'marketing_mode',
                'marketing_paused',
                'marketing_publishing_enabled'
            )
        """).fetchall()

    values = {row["key"]: row["value"] for row in rows}

    return {
        "mode": values.get("marketing_mode", "manual"),
        "paused": values.get("marketing_paused", "1") == "1",
        "publishing_enabled": False,
        "status": "PAUSED" if values.get(
            "marketing_paused", "1"
        ) == "1" else "READY",
    }


def set_marketing_control(mode=None, paused=None):
    if mode is not None and mode not in ("manual", "automatic"):
        return {"success": False, "message": "Invalid mode"}

    initialize_marketing_control()

    with connect() as db:
        if mode is not None:
            db.execute("""
                UPDATE settings
                SET value = ?
                WHERE key = 'marketing_mode'
            """, (mode,))

        if paused is not None:
            db.execute("""
                UPDATE settings
                SET value = ?
                WHERE key = 'marketing_paused'
            """, ("1" if paused else "0",))

        db.execute("""
            INSERT INTO activity_logs (action, details)
            VALUES (?, ?)
        """, (
            "marketing_control_updated",
            f"Mode={mode}; Paused={paused}; Publishing remains disabled"
        ))

    return {"success": True, "message": "Control updated"}
