from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_wtf.csrf import CSRFProtect
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("AGENT_SECRET", "change-this-secret-before-production")
csrf = CSRFProtect(app)

DB = "agent.db"

def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

init_db()

PAGE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Business AI Agent</title>
<style>
body{font-family:Arial;background:#f2f5fa;margin:0;color:#172033}
header{background:#172b4d;color:white;padding:22px}
main{padding:20px;max-width:850px;margin:auto}
.card{background:white;padding:18px;border-radius:14px;margin:14px 0;box-shadow:0 3px 12px #0001}
input,button{padding:13px;border-radius:8px;border:1px solid #ccd3df;width:100%;box-sizing:border-box;margin:7px 0}
button{background:#1769e0;color:white;border:0;font-weight:bold}
small{color:#64748b}
</style>
</head>
<body>
<header>
<h2>🤖 Business AI Agent</h2>
<p>One Agent · Multiple Businesses</p>
</header>
<main>
<div class="card">
<h3>Welcome to your AI Business Platform</h3>
<p>Manage multiple businesses from one dashboard.</p>
</div>
<div class="card">
<h3>Add New Business</h3>
<form method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<input name="name" placeholder="Business name" required>
<input name="category" placeholder="Business category">
<button type="submit">Add Business</button>
</form>
</div>
<div class="card">
<h3>Your Businesses</h3>
{% for b in businesses %}
<p><b>{{ b.name }}</b> — {{ b.category or 'Category not set' }}</p>
{% else %}
<p>No businesses added yet.</p>
{% endfor %}
</div>
</main>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def dashboard():
    con = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        if name:
            con.execute(
                "INSERT INTO businesses (name, category) VALUES (?, ?)",
                (name, category)
            )
            con.commit()
        con.close()
        return redirect(url_for("dashboard"))

    businesses = con.execute(
        "SELECT * FROM businesses ORDER BY id DESC"
    ).fetchall()
    con.close()
    return render_template_string(PAGE, businesses=businesses)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
