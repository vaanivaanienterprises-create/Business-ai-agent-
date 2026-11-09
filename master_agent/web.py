from flask import Flask, render_template_string, request, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from master_agent.core import get_agent_status
from master_agent.database import connect, init_db
from master_agent.tasks.manager import create_task
from master_agent.security.approval import review_approval
import os
import sqlite3
from pathlib import Path
from flask import session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from master_agent.providers.ai_engine import ask_openai, ask_claude

from master_agent.marketing.page import marketing_bp
from master_agent.control import control_bp
from master_agent.business_modules import business_bp

app = Flask(__name__)
SECRET_FILE = Path(__file__).resolve().parent.parent / ".master_secret"
if not SECRET_FILE.is_file():
    raise RuntimeError("Master secret missing")
app.secret_key = SECRET_FILE.read_text().strip()
if len(app.secret_key) < 64:
    raise RuntimeError("Invalid master secret")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1"
)
# LOGIN_SYSTEM_V1
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

class AdminUser(UserMixin):
    def __init__(self, user_id):
        self.id = str(user_id)

@login_manager.user_loader
def load_admin_user(user_id):
    with connect() as db:
        row = db.execute(
            "SELECT id FROM admin_users WHERE id = ?", (user_id,)
        ).fetchone()
    return AdminUser(row["id"]) if row else None

@app.before_request
def require_admin_login():
    if request.endpoint in ("login", "static"):
        return None
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
csrf = CSRFProtect(app)
app.register_blueprint(marketing_bp)
app.register_blueprint(control_bp)
app.register_blueprint(business_bp)

PAGE = """
<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet"
href="{{ url_for('static', filename='premium.css') }}">

<title>ApnaCare AI Master Agent</title>
<style>
body{font-family:Arial;background:#f1f5f9;color:#172033;margin:0}
header{background:#102b50;color:white;padding:20px}
main{max-width:900px;margin:auto;padding:14px}
.card{background:white;padding:17px;margin:13px 0;border-radius:13px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.number{font-size:25px;font-weight:bold;color:#1769e0}
small{color:#64748b}
input,textarea,select,button{width:100%;box-sizing:border-box;padding:12px;margin:6px 0;border:1px solid #ccd3df;border-radius:8px}
button{background:#1769e0;color:white;border:0;font-weight:bold}
.reject{background:#b42318}
.item{border-bottom:1px solid #eee;padding:10px 0}
.status{font-weight:bold;color:#16834a}
.warning{color:#b42318}
@media(max-width:500px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body class="premium-shell">
<aside class="premium-sidebar">
  <div class="premium-brand">
    <span class="brand-icon">✦</span>
    <div><b>ApnaCare</b><small>AI MASTER AGENT</small></div>
  </div>

  <div class="nav-heading">WORKSPACE</div>
  <a class="nav-link active" href="/">▦ Dashboard</a>
  <a class="nav-link" href="/marketing">✧ Marketing</a>

  <div class="nav-heading">BUSINESS</div>
  <div class="nav-link disabled">♡ Home Care <small>SOON</small></div>
  <a class="nav-link" href="/real-estate">⌂ Real Estate</a>
  <a class="nav-link" href="/tenders">▤ Government Tenders</a>

  <div class="nav-heading">MANAGEMENT</div>
  <a class="nav-link" href="/customers">♙ Customers</a>
  <a class="nav-link" href="/staff">♙ Staff Verification</a>
  <a class="nav-link" href="/bookings">▤ Bookings</a>
  <div class="nav-link disabled">◷ Reports <small>SOON</small></div>

  <div class="sidebar-footer">Premium Business Control<br><small>Apno Jaisi Care, Ghar Par.</small></div>
</aside>
<header>
<h2>🤖 ApnaCare AI Master Agent</h2>
<p>Business Management Control Center</p>
<form method="POST" action="/logout">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<button type="submit">Logout</button>
</form>
</header>
<main>

<div class="card">
<h3>🏢 ApnaCare Business Overview</h3>
<p>Database Connection:
<span class="status">{{ status.apnacare_status }}</span></p>

{% if status.apnacare_status == "CONNECTED" %}
<div class="grid">
<div class="card">
<small>Total Customers</small>
<div class="number">{{ status.apnacare_business.customers }}</div>
</div>
<div class="card">
<small>Total Bookings</small>
<div class="number">{{ status.apnacare_business.bookings }}</div>
</div>
<div class="card">
<small>Total Nurses / Staff</small>
<div class="number">{{ status.apnacare_business.nurses }}</div>
</div>
<div class="card">
<small>Pending Bookings</small>
<div class="number">{{ status.apnacare_business.statuses.get('Pending', 0) }}</div>
</div>
<div class="card">
<small>Completed Bookings</small>
<div class="number">{{ status.apnacare_business.statuses.get('Completed', 0) }}</div>
</div>
<div class="card">
<small>Cancelled Bookings</small>
<div class="number">{{ status.apnacare_business.statuses.get('Cancelled', 0) }}</div>
</div>
</div>
{% else %}
<p class="warning">ApnaCare database connection unavailable.</p>
{% endif %}
<p><small>Data is read-only. No customer or booking records are modified.</small></p>
</div>

<div class="grid">
<div class="card">
<small>Agent Database</small>
<div class="number">{{ status.database }}</div>
</div>
<div class="card">
<small>Total Tasks</small>
<div class="number">{{ status.tasks }}</div>
</div>
<div class="card">
<small>Pending Approvals</small>
<div class="number">{{ status.pending_approvals }}</div>
</div>
<div class="card">
<small>AI Providers</small>
<div class="number">2</div>
</div>
</div>

<div class="card">
<h3>📢 Marketing Agent</h3>
<p>WhatsApp और Facebook के लिए Hindi/English marketing drafts बनाएँ।</p>
<a href="/marketing" style="display:inline-block;background:#1769e0;color:white;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:bold">Open Marketing Agent</a>
<hr>
<h3>AI Provider Status</h3>
{% for name, info in status.providers.items() %}
<p><b>{{ name }}</b>: {{ info.status }}</p>
{% endfor %}
</div>

<div class="card">
<h3>➕ Create New Task</h3>
<form method="POST" action="/tasks">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<input name="title" placeholder="Task title" required>
<textarea name="description" placeholder="Task details"></textarea>
<select name="task_type">
<option value="general">General</option>
<option value="marketing">Marketing</option>
<option value="booking">Booking</option>
<option value="staff">Staff</option>
<option value="research">Research</option>
</select>
<button type="submit">Create Task</button>
</form>
</div>

<div class="card">
<h3>📋 Recent Tasks</h3>
{% for item in tasks %}
<div class="item">
<b>#{{ item.id }} — {{ item.title }}</b>
<p>{{ item.description }}</p>
<small>{{ item.task_type }} | {{ item.status }}</small>
</div>
{% else %}
<p>No tasks yet.</p>
{% endfor %}
</div>

<div class="card">
<h3>🔐 Approval Requests</h3>
{% for item in approvals %}
<div class="item">
<b>#{{ item.id }} — {{ item.action }}</b>
<p>{{ item.details }}</p>
<small>Status: {{ item.status }}</small>
{% if item.status == 'waiting' %}
<form method="POST" action="/approval/{{ item.id }}/approve">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<button type="submit">Approve</button>
</form>
<form method="POST" action="/approval/{{ item.id }}/reject">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<button class="reject" type="submit">Reject</button>
</form>
{% endif %}
</div>
{% else %}
<p>No approval requests.</p>
{% endfor %}
</div>

<div class="card">
<h3>Recent Activity</h3>
{% for item in logs %}
<div class="item">
<b>{{ item.action }}</b>
<p>{{ item.details }}</p>
<small>{{ item.created_at }}</small>
</div>
{% else %}
<p>No activity yet.</p>
{% endfor %}
</div>

<p><small>Local dashboard · Approval only · External actions are not executed</small></p>
</main>
</body>
</html>
"""



@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with connect() as db:
            row = db.execute(
                "SELECT id, password_hash FROM admin_users WHERE username = ?",
                (username,)
            ).fetchone()

        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            login_user(AdminUser(row["id"]), fresh=True)
            return redirect(url_for("dashboard"))

        error = "Username ya password galat hai."

    return render_template_string("""
    <!doctype html>
    <html lang="hi">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>ApnaCare AI Master Login</title>
      <style>
        body{font-family:Arial;background:#eef2f7;display:grid;place-items:center;min-height:100vh;margin:0}
        .card{background:white;padding:25px;border-radius:14px;width:min(340px,85%)}
        input,button{box-sizing:border-box;width:100%;padding:13px;margin:9px 0;border-radius:8px;border:1px solid #ccd3df}
        button{background:#1769e0;color:white;border:0;font-weight:bold}
        .error{color:#b42318}
      </style>
    </head>
    <body><div class="card">
      <h2>ApnaCare AI Master</h2>
      <p>Secure Admin Login</p>
      {% if error %}<p class="error">{{ error }}</p>{% endif %}
      <form method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input name="username" placeholder="Admin Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Login</button>
      </form>
    </div></body></html>
    """, error=error)


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
def dashboard():
    status = get_agent_status()

    with connect() as db:
        tasks = db.execute(
            "SELECT * FROM tasks ORDER BY id DESC LIMIT 10"
        ).fetchall()

        approvals = db.execute(
            "SELECT * FROM approval_requests ORDER BY id DESC LIMIT 10"
        ).fetchall()

        logs = db.execute(
            "SELECT * FROM activity_logs ORDER BY id DESC LIMIT 10"
        ).fetchall()

    return render_template_string(
        PAGE,
        status=status,
        tasks=tasks,
        approvals=approvals,
        logs=logs
    )


@app.route("/tasks", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    task_type = request.form.get("task_type", "general").strip()

    if title:
        create_task(title, description, task_type)

    return redirect(url_for("dashboard"))


@app.route("/approval/<int:request_id>/<decision>", methods=["POST"])
def handle_approval(request_id, decision):
    review_approval(request_id, decision)
    return redirect(url_for("dashboard"))



@app.route("/ai-chat", methods=["GET", "POST"])
def ai_chat():
    answer = ""
    error = ""
    question = ""
    provider = "openai"

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        provider = request.form.get("provider", "openai").strip().lower()

        if not question:
            error = "Pehle apna sawal likhiye."
        elif len(question) > 8000:
            error = "Sawal 8000 characters se chhota rakhein."
        elif provider not in ("openai", "claude"):
            error = "Invalid AI provider."
        else:
            result = ask_openai(question) if provider == "openai" else ask_claude(question)
            if result.get("ok"):
                answer = result.get("text", "")
            else:
                error = result.get("error", "AI request failed.")

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="hi">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="{{ url_for('static', filename='premium.css') }}">
      <title>ApnaCare AI Chat</title>
      <style>
        body{background:#07111f;color:#f5f5f5;font-family:Arial;margin:0;padding:18px}
        .chat{max-width:760px;margin:25px auto;background:#101d30;padding:22px;border:1px solid #b99545;border-radius:16px}
        h2{color:#e0bd68}
        textarea,select{box-sizing:border-box;width:100%;padding:13px;margin:10px 0;background:#07111f;color:white;border:1px solid #596579;border-radius:9px}
        button{background:#c6a04b;color:#101827;padding:13px 20px;border:0;border-radius:9px;font-weight:bold}
        .answer,.error{white-space:pre-wrap;padding:14px;margin-top:18px;border-radius:9px;overflow-wrap:anywhere}
        .answer{background:#172b3d;border:1px solid #c6a04b}
        .error{background:#3a2025;color:#ffd5d5}
        a{color:#e0bd68}
      </style>
    </head>
    <body>
      <div class="chat">
        <h2>ApnaCare AI Master Chat</h2>
        <p>Apne business ke sawal AI se poochhiye.</p>
        <form method="POST">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <label>AI Provider</label>
          <select name="provider">
            <option value="openai" {% if provider == 'openai' %}selected{% endif %}>OpenAI</option>
            <option value="claude" {% if provider == 'claude' %}selected{% endif %}>Claude</option>
          </select>
          <label>Aapka sawal</label>
          <textarea name="question" rows="5" maxlength="8000" placeholder="Apna sawal yahan likhein..." required>{{ question }}</textarea>
          <button type="submit">AI se jawab lein</button>
        </form>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if answer %}<div class="answer"><b>AI Response:</b><br><br>{{ answer }}</div>{% endif %}
        <p><a href="/">Dashboard par wapas jaayein</a></p>
        <small>AI responses may be inaccurate. External actions are not executed from this chat.</small>
      </div>
    </body>
    </html>
    """, answer=answer, error=error, question=question, provider=provider)



# CUSTOMER_BOOKING_V1
def get_apnacare_rows(query, params=()):
    db_path = Path(os.environ.get("APNACARE_DB_PATH", str(Path.home() / "apnacare" / "apnacare.db")))
    if not db_path.is_file():
        raise FileNotFoundError("ApnaCare database unavailable")

    uri = db_path.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=5) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(query, params).fetchall()]


@app.route("/customers")
def customers_page():
    rows = get_apnacare_rows(
        "SELECT id, name, phone, address, created_at "
        "FROM customers ORDER BY id DESC LIMIT 200"
    )
    return render_template_string("""
    <!doctype html><html lang="hi"><head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>ApnaCare Customers</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='premium.css') }}">
    <style>
    body{font-family:Arial;background:#f1f5f9;color:#172033;padding:15px}
    .wrap{max-width:900px;margin:auto}.card{background:white;padding:16px;margin:12px 0;border-radius:12px}
    .item{padding:12px 0;border-bottom:1px solid #eee}
    a{color:#1769e0}
    </style></head><body><div class="wrap">
    <h2>♙ Customer Management</h2>
    <p>Total customers: <b>{{ rows|length }}</b> (maximum 200 shown)</p>
    <div class="card">
    {% for r in rows %}
    <div class="item">
    <b>{{ r.name }}</b> · ID {{ r.id }}<br>
    Phone: {{ r.phone }}<br>
    Address: {{ r.address or 'Not provided' }}<br>
    <small>{{ r.created_at or '' }}</small>
    </div>
    {% else %}<p>No customers found.</p>{% endfor %}
    </div>
    <p>Read-only view. Customer passwords are never displayed.</p>
    <a href="/">← Dashboard</a> · <a href="/bookings">Bookings</a>
    </div></body></html>
    """, rows=rows)


@app.route("/bookings")
def bookings_page():
    rows = get_apnacare_rows(
        "SELECT id, name, phone, service, age, address, date, time, "
        "details, status, created_at FROM bookings ORDER BY id DESC LIMIT 200"
    )
    return render_template_string("""
    <!doctype html><html lang="hi"><head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>ApnaCare Bookings</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='premium.css') }}">
    <style>
    body{font-family:Arial;background:#f1f5f9;color:#172033;padding:15px}
    .wrap{max-width:900px;margin:auto}.card{background:white;padding:16px;margin:12px 0;border-radius:12px}
    .item{padding:14px 0;border-bottom:1px solid #eee}
    a{color:#1769e0}.status{font-weight:bold}
    </style></head><body><div class="wrap">
    <h2>▤ Booking Management</h2>
    <p>Bookings shown: <b>{{ rows|length }}</b> (maximum 200)</p>
    <div class="card">
    {% for r in rows %}
    <div class="item">
    <b>Booking #{{ r.id }} — {{ r.name }}</b><br>
    Phone: {{ r.phone }}<br>
    Service: {{ r.service }}<br>
    Date: {{ r.date }} · Time: {{ r.time }}<br>
    Status: <span class="status">{{ r.status }}</span><br>
    Address: {{ r.address or 'Not provided' }}<br>
    <small>Age: {{ r.age or 'Not provided' }} · {{ r.created_at or '' }}</small>
    {% if r.details %}<p>{{ r.details }}</p>{% endif %}
    </div>
    {% else %}<p>No bookings found.</p>{% endfor %}
    </div>
    <p>Read-only view. No booking records are modified.</p>
    <a href="/">← Dashboard</a> · <a href="/customers">Customers</a>
    </div></body></html>
    """, rows=rows)




# STAFF_VERIFICATION_V2
def write_staff_audit(action, details):
    with connect() as db:
        db.execute(
            "INSERT INTO activity_logs (action, details) VALUES (?, ?)",
            (action, details)
        )


@app.route("/staff", methods=["GET"])
def staff_page():
    rows = get_apnacare_rows("""
        SELECT id, name, phone, service, experience, status,
               id_proof_type, id_proof_status,
               police_status, training_status, verification_notes
        FROM nurses ORDER BY id DESC LIMIT 200
    """)

    staff = []
    for r in rows:
        eligible = (
            r["id_proof_status"] == "Verified"
            and r["police_status"] == "Verified"
            and r["training_status"] == "Completed"
        )
        staff.append({"data": r, "eligible": eligible})

    return render_template_string("""
    <!doctype html><html lang="hi"><head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>ApnaCare Staff Verification</title>
    <style>
    body{font-family:Arial;background:#f1f5f9;padding:15px;color:#172033}
    .wrap{max-width:850px;margin:auto}
    .card{background:white;padding:16px;border-radius:12px;margin:12px 0}
    .item{padding:14px 0;border-bottom:1px solid #ddd}
    input,select,button{box-sizing:border-box;width:100%;padding:10px;margin:6px 0}
    button{background:#1769e0;color:white;border:0;border-radius:7px}
    .yes{color:#16834a;font-weight:bold}.no{color:#b42318;font-weight:bold}
    </style></head><body><div class="wrap">
    <h2>ApnaCare Staff Verification</h2>
    <p>Total Staff: {{ staff|length }}</p>
    {% for item in staff %}
      {% set r = item.data %}
      <div class="card">
        <h3>{{ r.name }} — Staff #{{ r.id }}</h3>
        <p>Phone: {{ r.phone }} | Service: {{ r.service }}</p>
        <p>Current Status: <b>{{ r.status }}</b></p>
        <form method="POST" action="{{ url_for('update_staff_verification', staff_id=r.id) }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <label>ID Proof</label>
          <select name="id_proof_status">
            {% for v in ['Pending','Verified','Rejected'] %}
            <option value="{{ v }}" {% if r.id_proof_status == v %}selected{% endif %}>{{ v }}</option>
            {% endfor %}
          </select>
          <label>Police Verification</label>
          <select name="police_status">
            {% for v in ['Pending','Verified','Rejected'] %}
            <option value="{{ v }}" {% if r.police_status == v %}selected{% endif %}>{{ v }}</option>
            {% endfor %}
          </select>
          <label>Training</label>
          <select name="training_status">
            {% for v in ['Not Started','In Progress','Completed','Rejected'] %}
            <option value="{{ v }}" {% if r.training_status == v %}selected{% endif %}>{{ v }}</option>
            {% endfor %}
          </select>
          <label>Verification Notes</label>
          <input name="verification_notes" maxlength="1000"
                 value="{{ r.verification_notes or '' }}" placeholder="Verification notes">
          <button type="submit">Save Verification</button>
        </form>
        {% if item.eligible %}
          <p class="yes">All checks passed — eligible for approval.</p>
          {% if r.status != 'Approved' %}
          <form method="POST" action="{{ url_for('approve_staff', staff_id=r.id) }}">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <button type="submit">Approve Staff</button>
          </form>
          {% endif %}
        {% else %}
          <p class="no">Not eligible — all three checks must pass.</p>
        {% endif %}
      </div>
    {% else %}
      <div class="card">No staff found.</div>
    {% endfor %}
    <p><a href="/">Back to Dashboard</a></p>
    </div></body></html>
    """, staff=staff)


@app.route("/staff/<int:staff_id>/verification", methods=["POST"])
def update_staff_verification(staff_id):
    id_status = request.form.get("id_proof_status", "")
    police = request.form.get("police_status", "")
    training = request.form.get("training_status", "")
    notes = request.form.get("verification_notes", "").strip()

    if id_status not in ("Pending", "Verified", "Rejected"):
        return "Invalid ID Proof status", 400
    if police not in ("Pending", "Verified", "Rejected"):
        return "Invalid Police status", 400
    if training not in ("Not Started", "In Progress", "Completed", "Rejected"):
        return "Invalid Training status", 400
    if len(notes) > 1000:
        return "Notes too long", 400

    db_path = Path(os.environ.get("APNACARE_DB_PATH", str(Path.home() / "apnacare" / "apnacare.db")))
    with sqlite3.connect(db_path, timeout=5) as db:
        row = db.execute(
            "SELECT status FROM nurses WHERE id=?", (staff_id,)
        ).fetchone()
        if not row:
            return "Staff not found", 404

        new_status = row[0]
        if not (
            id_status == "Verified"
            and police == "Verified"
            and training == "Completed"
        ):
            new_status = "Pending"

        db.execute("""
            UPDATE nurses
            SET id_proof_status=?, police_status=?,
                training_status=?, verification_notes=?,
                status=?, verified_at=CASE WHEN ?='Pending' THEN '' ELSE verified_at END
            WHERE id=?
        """, (id_status, police, training, notes, new_status, new_status, staff_id))

    write_staff_audit(
        "staff_verification_updated",
        f"Staff ID {staff_id}: ID={id_status}, Police={police}, Training={training}"
    )
    return redirect(url_for("staff_page"))


@app.route("/staff/<int:staff_id>/approve", methods=["POST"])
def approve_staff(staff_id):
    db_path = Path(os.environ.get("APNACARE_DB_PATH", str(Path.home() / "apnacare" / "apnacare.db")))
    with sqlite3.connect(db_path, timeout=5) as db:
        row = db.execute("""
            SELECT id_proof_status, police_status, training_status
            FROM nurses WHERE id=?
        """, (staff_id,)).fetchone()

        if not row:
            return "Staff not found", 404

        if not (
            row[0] == "Verified"
            and row[1] == "Verified"
            and row[2] == "Completed"
        ):
            return "Approval blocked: all three checks are mandatory.", 403

        db.execute("""
            UPDATE nurses SET status='Approved',
            verified_at=CURRENT_TIMESTAMP WHERE id=?
        """, (staff_id,))

    write_staff_audit("staff_approved", f"Staff ID {staff_id} approved by admin")
    return redirect(url_for("staff_page"))


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5055, debug=False)
