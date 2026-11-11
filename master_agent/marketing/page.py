from flask import Blueprint, render_template_string, request
from master_agent.marketing.content import generate_marketing_content
from master_agent.database import connect
import json

marketing_bp = Blueprint("marketing", __name__)

MARKETING_PAGE = """
<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet"
href="{{ url_for('static', filename='premium.css') }}">

<title>ApnaCare Marketing Agent</title>
<style>
body{font-family:Arial;background:#f1f5f9;margin:0;padding:15px;color:#172033}
.card{background:white;padding:18px;margin:12px auto;border-radius:12px;max-width:700px}
input,select,button,textarea{box-sizing:border-box;width:100%;padding:12px;margin:7px 0;border:1px solid #ccd3df;border-radius:8px}
button{background:#1769e0;color:white;border:0;font-weight:bold}
textarea{min-height:150px}
a{color:#1769e0}
</style>
</head>
<body>
<div class="card">
<h2>📢 ApnaCare Marketing Agent</h2>
<a href="/">← Dashboard पर वापस जाएँ</a>
<form method="POST">
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
<label>Service चुनें</label>
<select name="service">
{% for s in services %}
<option value="{{ s }}" {% if selected_service == s %}selected{% endif %}>{{ s }}</option>
{% endfor %}
</select>
<label>भाषा चुनें</label>
<select name="language">
<option value="Hindi" {% if language == "Hindi" %}selected{% endif %}>Hindi</option>
<option value="English" {% if language == "English" %}selected{% endif %}>English</option>
</select>
<button type="submit">Marketing Draft बनाएँ</button>
</form>
{% if result %}
<h3>WhatsApp Draft</h3>
<textarea readonly>{{ result.whatsapp_draft }}</textarea>
<h3>Facebook Draft</h3>
<textarea readonly>{{ result.facebook_draft }}</textarea>
<h3>Instagram Caption + Hashtags</h3>
<textarea readonly>{{ result.instagram_draft }}</textarea>
<p><b>{{ result.status }}</b></p>
{% if result.approval_request_id %}
<div style="background:#e8f5e9;color:#173b2b;padding:12px;border-radius:8px">
<b>✅ Draft Approval Queue में सेव हो गया!</b>
<p>Approval Request ID: #{{ result.approval_request_id }}</p>
<p>Status: Waiting for Admin Approval</p>
<p>यह पोस्ट अभी प्रकाशित नहीं हुई है।</p>
</div>
{% endif %}

{% endif %}
</div>
</body>
</html>
"""

@marketing_bp.route("/marketing", methods=["GET", "POST"])
def marketing_page():
    services = ["Home Nursing", "Elder Care", "Patient Care", "Baby Care", "Caregiver Service"]
    service = request.form.get("service", "Home Nursing")
    language = request.form.get("language", "Hindi")
    result = None
    if request.method == "POST":
        result = generate_marketing_content(service, language)

        if result:
            details = json.dumps({
                "service": result["service"],
                "language": result["language"],
                "whatsapp_draft": result["whatsapp_draft"],
                "facebook_draft": result["facebook_draft"],
                "instagram_draft": result["instagram_draft"],
                "provider": result.get("provider", "Template"),
                "note": "Draft only. Approval does not publish automatically."
            }, ensure_ascii=False, indent=2)

            with connect() as db:
                cursor = db.execute(
                    "INSERT INTO approval_requests (action, details) VALUES (?, ?)",
                    ("marketing_draft_review", details)
                )
                result["approval_request_id"] = cursor.lastrowid
                db.execute(
                    "INSERT INTO activity_logs (action, details) VALUES (?, ?)",
                    ("marketing_draft_created",
                     f"Approval request #{cursor.lastrowid}")
                )
    return render_template_string(
        MARKETING_PAGE,
        services=services,
        selected_service=service,
        language=language,
        result=result
    )
