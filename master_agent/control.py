from flask import Blueprint, render_template_string, request
from master_agent.providers.status import get_provider_status
from master_agent.tasks.manager import submit_action

control_bp = Blueprint("control", __name__)

ACTIONS = {
    "research": "Research",
    "generate_report": "Generate Report",
    "draft_message": "Draft Message",
    "create_task": "Create Task",
    "send_message": "Send Message",
    "modify_code": "Modify Code",
    "make_payment": "Make Payment",
    "deploy": "Deploy",
    "submit_tender": "Submit Tender",
}

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ApnaCare AI Control Center</title>
<link rel="stylesheet"
href="{{ url_for('static', filename='premium.css') }}">
</head>
<body>
<main>
<div class="card">
<h2>🤖 ApnaCare AI Control Center</h2>
<p>Secure Business Automation</p>
<a href="/">Back to Dashboard</a>
</div>

<div class="card">
<h3>AI Provider Connections</h3>
{% for name, info in providers.items() %}
<p><b>{{ name }}</b>: {{ info.status }}</p>
{% endfor %}
</div>

<div class="card">
<h3>Security Status</h3>
<p class="status">Safe Actions: Allowed</p>
<p class="warning">Sensitive Actions: Approval Required</p>
</div>

<div class="card">
<h3>Request AI Action</h3>
<form method="POST" action="/control/request">
<input type="hidden" name="csrf_token"
value="{{ csrf_token() }}">
<select name="action" required>
{% for key, label in actions.items() %}
<option value="{{ key }}">{{ label }}</option>
{% endfor %}
</select>
<textarea name="details" required
placeholder="Describe your task"></textarea>
<button type="submit">Submit Request</button>
</form>

{% if result %}
<h3>Request Result</h3>
<p>{{ result.status }}</p>
<p>{{ result.message }}</p>
{% endif %}
</div>
</main>
</body>
</html>
"""

@control_bp.route("/control")
def control_home():
    return render_template_string(
        PAGE,
        providers=get_provider_status(),
        actions=ACTIONS,
        result=None
    )

@control_bp.route("/control/request", methods=["POST"])
def control_request():
    action = request.form.get("action", "").strip()
    details = request.form.get("details", "").strip()

    if action not in ACTIONS or not details:
        result = {
            "status": "Invalid",
            "message": "Invalid action or empty details."
        }
    else:
        result = submit_action(action, details)

    return render_template_string(
        PAGE,
        providers=get_provider_status(),
        actions=ACTIONS,
        result=result
    )
