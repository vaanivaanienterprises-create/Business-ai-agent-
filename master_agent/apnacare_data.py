import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "apnacare" / "apnacare.db"


def get_business_summary():
    if not DB_PATH.exists():
        raise FileNotFoundError("ApnaCare database not found")

    uri = DB_PATH.as_uri() + "?mode=ro"

    with sqlite3.connect(uri, uri=True, timeout=5) as db:
        customers = db.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        bookings = db.execute(
            "SELECT COUNT(*) FROM bookings"
        ).fetchone()[0]

        nurses = db.execute(
            "SELECT COUNT(*) FROM nurses"
        ).fetchone()[0]

        statuses = db.execute(
            "SELECT status, COUNT(*) FROM bookings GROUP BY status"
        ).fetchall()

    return {
        "customers": customers,
        "bookings": bookings,
        "nurses": nurses,
        "statuses": dict(statuses)
    }


if __name__ == "__main__":
    print(get_business_summary())
