"""Admin-only local handoff for preparing planned posts for Metricool."""

from pathlib import Path

from flask import Blueprint, flash, redirect, render_template_string, request, url_for
from master_agent.database import connect

handoff_bp = Blueprint("handoff", __name__)

MEDIA_DIR = (
    Path(__file__).resolve().parents[1]
    / "static" / "uploads" / "media"
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4"}

HANDOFF_PAGE = """
<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Metricool Handoff - ApnaCare</title>
<style>
body{font-family:Arial;background:#f1f5f9;color:#172033;margin:0;padding:15px}
.wrap{max-width:850px;margin:auto}
.card{background:white;padding:17px;margin:13px 0;border-radius:13px}
textarea,select,button{box-sizing:border-box;width:100%;padding:12px;margin:7px 0;border:1px solid #ccd3df;border-radius:8px}
textarea{min-height:130px}
button{background:#1769e0;color:white;border:0;font-weight:bold}
a{color:#1769e0;overflow-wrap:anywhere}
.notice{background:#e8f5e9;padding:10px;border-radius:8px}
.error{background:#fee2e2;padding:10px;border-radius:8px}
.meta{color:#64748b;font-size:14px}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h2>ApnaCare – Metricool Handoff</h2>
<p><a href="/">Dashboard</a> | <a href="/media">Media Manager</a></p>
<p>यहाँ planned पोस्ट के लिए media चुनें। इससे केवल local database में media path जुड़ेगा। कोई पोस्ट schedule या publish नहीं होगी।</p>
</div>

{% with messages = get_flashed_messages(with_categories=true) %}
{% for category, message in messages %}
<div class="{{ 'error' if category == 'error' else 'notice' }}">{{ message }}</div>
{% endfor %}
{% endwith %}

{% for post in posts %}
<div class="card">
<h3>{{ post.platform }} – Post #{{ post.id }}</h3>
<p class="meta">Status: {{ post.status }} | Schedule: {{ post.scheduled_at or "अभी तय नहीं" }}</p>
<label>Caption</label>
<textarea readonly>{{ post.caption }}</textarea>

{% if post.media_path %}
<p>मौजूदा media: {{ post.media_path }}</p>
{% else %}
<p class="meta">अभी इस पोस्ट से media नहीं जुड़ा है।</p>
{% endif %}

{% if media_files %}
<form method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<input type="hidden" name="post_id" value="{{ post.id }}">
<label>Uploaded media चुनें</label>
<select name="media_filename" required>
<option value="">-- Media चुनें --</option>
{% for item in media_files %}
<option value="{{ item.name }}" {% if post.media_path and post.media_path.endswith(item.name) %}selected{% endif %}>
{{ item.name }} ({{ item.kind }})
</option>
{% endfor %}
</select>
<button type="submit">इस पोस्ट से Media जोड़ें</button>
</form>
{% else %}
<p>पहले <a href="/media">Media Manager</a> में promotional image या video upload करें।</p>
{% endif %}
</div>
{% else %}
<div class="card"><p>अभी कोई planned या approved पोस्ट नहीं मिली।</p></div>
{% endfor %}

<div class="card">
<p><strong>अगला चरण:</strong> Media जुड़ने के बाद उसे फोन में डाउनलोड करके ChatGPT में attach करेंगे और आपकी अनुमति के बाद Metricool scheduling करेंगे।</p>
</div>
</div>
</body>
</html>
"""


@handoff_bp.route("/metricool-handoff", methods=["GET", "POST"])
def metricool_handoff():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    if request.method == "POST":
        try:
            post_id = int(request.form.get("post_id", ""))
        except (TypeError, ValueError):
            flash("Post ID सही नहीं है।", "error")
            return redirect(url_for("handoff.metricool_handoff"))

        filename = request.form.get("media_filename", "")
        candidate = MEDIA_DIR / filename

        if (
            not filename
            or Path(filename).name != filename
            or Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS
            or not candidate.is_file()
            or candidate.resolve().parent != MEDIA_DIR.resolve()
        ):
            flash("चुनी गई media file मान्य नहीं है।", "error")
            return redirect(url_for("handoff.metricool_handoff"))

        relative_path = f"uploads/media/{filename}"

        with connect() as db:
            cursor = db.execute(
                """
                UPDATE marketing_posts
                SET media_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status IN ('planned', 'approved')
                """,
                (relative_path, post_id),
            )

            if cursor.rowcount != 1:
                flash("Post नहीं मिली या उसका status बदल चुका है।", "error")
            else:
                db.execute(
                    "INSERT INTO activity_logs (action, details) VALUES (?, ?)",
                    ("metricool_media_attached", f"Post {post_id}: {filename}"),
                )
                flash("Media इस पोस्ट से जोड़ दी गई। अभी कोई scheduling या publishing नहीं हुई।", "success")

        return redirect(url_for("handoff.metricool_handoff"))

    with connect() as db:
        posts = db.execute(
            """
            SELECT id, platform, caption, status, scheduled_at, media_path
            FROM marketing_posts
            WHERE status IN ('planned', 'approved')
            ORDER BY id DESC
            """
        ).fetchall()

    media_files = []
    for path in sorted(MEDIA_DIR.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in ALLOWED_EXTENSIONS:
            media_files.append({
                "name": path.name,
                "kind": "video" if path.suffix.lower() == ".mp4" else "image",
            })

    return render_template_string(
        HANDOFF_PAGE,
        posts=posts,
        media_files=media_files,
    )
