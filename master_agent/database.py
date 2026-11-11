import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "master_agent.db"


def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            task_type TEXT DEFAULT 'general',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS approval_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT DEFAULT '',
            status TEXT DEFAULT 'waiting',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );
        """)

        db.executescript("""
            CREATE TABLE IF NOT EXISTS marketing_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'post',
                caption TEXT DEFAULT '',
                media_path TEXT DEFAULT '',
                thumbnail_path TEXT DEFAULT '',
                scheduled_at TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                remote_post_id TEXT DEFAULT '',
                published_at TEXT,
                error_message TEXT DEFAULT '',
                metrics_json TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS marketing_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT NOT NULL,
                run_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                payload_json TEXT DEFAULT '{}',
                last_error TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS marketing_platforms (
                platform TEXT PRIMARY KEY,
                account_name TEXT DEFAULT '',
                connection_status TEXT NOT NULL DEFAULT 'not_connected',
                credential_ref TEXT DEFAULT '',
                last_checked TEXT,
                last_error TEXT DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_marketing_posts_status_schedule
            ON marketing_posts(status, scheduled_at);

            CREATE INDEX IF NOT EXISTS idx_marketing_jobs_status_run_at
            ON marketing_jobs(status, run_at);
        """)

        for platform in (
            "Facebook",
            "Google Business Profile",
            "Instagram",
            "JustDial",
            "WhatsApp Business",
            "YouTube",
        ):
            db.execute(
                "INSERT OR IGNORE INTO marketing_platforms (platform) VALUES (?)",
                (platform,)
            )


if __name__ == "__main__":
    init_db()
    print("ApnaCare Master Agent Database: READY")
    print(f"Database: {DB_PATH}")
