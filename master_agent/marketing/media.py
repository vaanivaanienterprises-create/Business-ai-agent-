"""Admin-only media upload and preview for ApnaCare AI Master."""

from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template_string,
    request,
    url_for,
)
from werkzeug.utils import secure_filename


media_bp = Blueprint("media", __name__)

MEDIA_DIR = (
    Path(__file__).resolve().parents[1]
    / "static"
    / "uploads"
    / "media"
)

IMAGE_LIMIT = 10 * 1024 * 1024
VIDEO_LIMIT = 100 * 1024 * 1024

ALLOWED_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
}


def detect_file_type(header):
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"

    if (
        len(header) >= 12
        and header[:4] == b"RIFF"
        and header[8:12] == b"WEBP"
    ):
        return ".webp"

    if len(header) >= 12 and header[4:8] == b"ftyp":
        return ".mp4"

    return None


MEDIA_PAGE = """
<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ApnaCare Media Manager</title>
<style>
body{font-family:Arial;background:#f1f5f9;color:#172033;margin:0;padding:15px}
.card{background:white;padding:18px;margin:12px auto;border-radius:12px;max-width:760px}
input,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0;border:1px solid #ccd3df;border-radius:8px}
button{background:#1769e0;color:white;border:0;font-weight:bold}
.item{border-top:1px solid #ddd;padding:14px 0}
img,video{width:100%;max-height:320px;object-fit:contain;background:#e5e7eb}
a{color:#1769e0;overflow-wrap:anywhere}
.notice{padding:10px;background:#e8f5e9;border-radius:8px}
.error{padding:10px;background:#fee2e2;border-radius:8px}
</style>
</head>
<body>
<div class="card">
<h2>ApnaCare Media Manager</h2>
<p><a href="/">Dashboard पर वापस जाएँ</a></p>

<p>JPG, JPEG, PNG, WEBP: अधिकतम 10 MB</p>
<p>MP4 Video: अधिकतम 100 MB</p>

<form method="POST" enctype="multipart/form-data">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<input type="file" name="media_file" accept=".jpg,.jpeg,.png,.webp,.mp4" required>
<button type="submit">Upload Media</button>
</form>

{% with messages = get_flashed_messages(with_categories=true) %}
{% for category, message in messages %}
<div class="{{ 'error' if category == 'error' else 'notice' }}">{{ message }}</div>
{% endfor %}
{% endwith %}
</div>

<div class="card">
<h3>Uploaded Media</h3>
{% for item in items %}
<div class="item">
<strong>{{ item.name }}</strong>
{% if item.kind == "image" %}
<img src="{{ item.url }}" alt="Uploaded ApnaCare media">
{% else %}
<video controls preload="metadata">
<source src="{{ item.url }}" type="video/mp4">
</video>
{% endif %}
<p><a href="{{ item.url }}" target="_blank" rel="noopener">Open Media Link</a></p>
</div>
{% else %}
<p>अभी कोई media upload नहीं हुआ है।</p>
{% endfor %}
</div>
</body>
</html>
"""


@media_bp.route("/media", methods=["GET", "POST"])
def media_manager():
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    if request.method == "POST":
        uploaded = request.files.get("media_file")

        if not uploaded or not uploaded.filename:
            flash("कृपया image या MP4 video चुनें।", "error")
            return redirect(url_for("media.media_manager"))

        original_name = secure_filename(uploaded.filename)
        extension = Path(original_name).suffix.lower()

        if extension not in ALLOWED_TYPES:
            flash("यह file format स्वीकार नहीं है।", "error")
            return redirect(url_for("media.media_manager"))

        limit = VIDEO_LIMIT if extension == ".mp4" else IMAGE_LIMIT
        temporary_path = None

        try:
            header = uploaded.stream.read(16)
            detected_extension = detect_file_type(header)

            if detected_extension is None:
                flash("File का वास्तविक format पहचाना नहीं गया।", "error")
                return redirect(url_for("media.media_manager"))

            if extension in (".jpg", ".jpeg"):
                extension_matches = detected_extension == ".jpg"
            else:
                extension_matches = extension == detected_extension

            if not extension_matches:
                flash("File extension और वास्तविक format अलग हैं।", "error")
                return redirect(url_for("media.media_manager"))

            safe_name = f"{uuid4().hex}{extension}"
            final_path = MEDIA_DIR / safe_name
            temporary_path = MEDIA_DIR / f".{uuid4().hex}.tmp"

            total = len(header)

            with temporary_path.open("xb") as output:
                output.write(header)

                while True:
                    chunk = uploaded.stream.read(1024 * 1024)
                    if not chunk:
                        break

                    total += len(chunk)

                    if total > limit:
                        raise ValueError("File निर्धारित size limit से बड़ी है।")

                    output.write(chunk)

            temporary_path.replace(final_path)
            flash("Media सफलतापूर्वक upload हो गया।", "success")

        except ValueError as exc:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()
            flash(str(exc), "error")

        except OSError:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()
            current_app.logger.exception("Media upload failed")
            flash("Upload पूरा नहीं हुआ। Storage और permissions जाँचें।", "error")

        return redirect(url_for("media.media_manager"))

    items = []

    for path in sorted(
        MEDIA_DIR.iterdir(),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        if not path.is_file() or path.name.startswith("."):
            continue

        extension = path.suffix.lower()

        if extension not in ALLOWED_TYPES:
            continue

        items.append({
            "name": path.name,
            "kind": "video" if extension == ".mp4" else "image",
            "url": url_for(
                "static",
                filename=f"uploads/media/{path.name}",
            ),
        })

        if len(items) >= 30:
            break

    return render_template_string(MEDIA_PAGE, items=items)
