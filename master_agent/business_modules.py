from flask import Blueprint, request, redirect, url_for, render_template_string
from master_agent.database import connect

business_bp = Blueprint("business", __name__)

STYLE = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/static/premium.css">
<style>
body{font-family:Arial;background:#f1f5f9;color:#172033;padding:15px}
.wrap{max-width:1050px;margin:auto}
.card{background:white;padding:16px;margin:14px 0;border-radius:12px}
input,select,textarea,button{box-sizing:border-box;width:100%;padding:11px;margin:6px 0;border:1px solid #ccd3df;border-radius:8px}
button{background:#1769e0;color:white;border:0;font-weight:bold}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.item{padding:12px 0;border-bottom:1px solid #eee}
a{color:#1769e0}
</style>
"""

@business_bp.route("/real-estate", methods=["GET", "POST"])
def real_estate():
    message = ""
    if request.method == "POST":
        action = request.form.get("action")

        if action == "property":
            title = request.form.get("title", "").strip()
            if not title:
                message = "Property title is required."
            else:
                with connect() as db:
                    db.execute("""
                        INSERT INTO properties
                        (title, property_type, listing_type, price, area,
                         address, owner_name, owner_phone, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title,
                        request.form.get("property_type", "House"),
                        request.form.get("listing_type", "Sell"),
                        float(request.form.get("price") or 0),
                        request.form.get("area", "").strip(),
                        request.form.get("address", "").strip(),
                        request.form.get("owner_name", "").strip(),
                        request.form.get("owner_phone", "").strip(),
                        request.form.get("description", "").strip()
                    ))
                return redirect(url_for("business.real_estate"))

        elif action == "lead":
            name = request.form.get("name", "").strip()
            if not name:
                message = "Customer name is required."
            else:
                with connect() as db:
                    db.execute("""
                        INSERT INTO property_leads
                        (name, phone, requirement, budget, area, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        name,
                        request.form.get("phone", "").strip(),
                        request.form.get("requirement", "").strip(),
                        float(request.form.get("budget") or 0),
                        request.form.get("area", "").strip(),
                        request.form.get("notes", "").strip()
                    ))
                return redirect(url_for("business.real_estate"))

    with connect() as db:
        properties = db.execute(
            "SELECT * FROM properties ORDER BY id DESC LIMIT 100"
        ).fetchall()
        leads = db.execute(
            "SELECT * FROM property_leads ORDER BY id DESC LIMIT 100"
        ).fetchall()

    return render_template_string("""
    <!doctype html><html><head><title>Real Estate</title>""" + STYLE + """</head>
    <body><div class="wrap">
    <h2>⌂ Real Estate Management</h2>
    <p>Property listings and customer enquiries</p>
    {% if message %}<p>{{ message }}</p>{% endif %}
    <div class="grid">
      <div class="card"><h3>Add Property</h3>
        <form method="POST">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <input type="hidden" name="action" value="property">
          <input name="title" placeholder="Property title" required>
          <select name="property_type">
            <option>House</option><option>Plot</option><option>Flat</option>
            <option>Shop</option><option>Office</option><option>Land</option>
          </select>
          <select name="listing_type">
            <option>Sell</option><option>Rent</option><option>Lease</option>
          </select>
          <input name="price" type="number" min="0" step="0.01" placeholder="Price / Rent in INR">
          <input name="area" placeholder="Area / Locality">
          <input name="address" placeholder="Full address">
          <input name="owner_name" placeholder="Owner name">
          <input name="owner_phone" placeholder="Owner phone">
          <textarea name="description" placeholder="Property details"></textarea>
          <button type="submit">Save Property</button>
        </form>
      </div>
      <div class="card"><h3>Add Customer Lead</h3>
        <form method="POST">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <input type="hidden" name="action" value="lead">
          <input name="name" placeholder="Customer name" required>
          <input name="phone" placeholder="Phone">
          <select name="requirement">
            <option>Buy</option><option>Rent</option><option>Sell</option>
            <option>Commercial</option>
          </select>
          <input name="budget" type="number" min="0" placeholder="Budget in INR">
          <input name="area" placeholder="Preferred area">
          <textarea name="notes" placeholder="Notes"></textarea>
          <button type="submit">Save Lead</button>
        </form>
      </div>
    </div>
    <div class="card"><h3>Properties ({{ properties|length }})</h3>
    {% for p in properties %}
      <div class="item"><b>#{{ p.id }} — {{ p.title }}</b>
      <br>{{ p.property_type }} · {{ p.listing_type }} · ₹{{ p.price }}
      <br>{{ p.area }} · {{ p.address }}
      <br>Owner: {{ p.owner_name }} · {{ p.owner_phone }}
      <br>Status: {{ p.status }}</div>
    {% else %}<p>No properties added yet.</p>{% endfor %}
    </div>
    <div class="card"><h3>Customer Leads ({{ leads|length }})</h3>
    {% for l in leads %}
      <div class="item"><b>#{{ l.id }} — {{ l.name }}</b>
      <br>{{ l.phone }} · {{ l.requirement }} · Budget ₹{{ l.budget }}
      <br>{{ l.area }} · {{ l.status }}<br>{{ l.notes }}</div>
    {% else %}<p>No leads added yet.</p>{% endfor %}
    </div>
    <p><a href="/">← Back to Dashboard</a></p>
    </div></body></html>
    """, properties=properties, leads=leads, message=message)


@business_bp.route("/tenders", methods=["GET", "POST"])
def tenders():
    message = ""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            message = "Tender title is required."
        else:
            with connect() as db:
                cursor = db.execute("""
                    INSERT INTO tenders
                    (title, department, tender_reference, location,
                     estimated_value, emd_amount, fee_amount, deadline,
                     source_url, eligibility_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title,
                    request.form.get("department", "").strip(),
                    request.form.get("tender_reference", "").strip(),
                    request.form.get("location", "").strip(),
                    float(request.form.get("estimated_value") or 0),
                    float(request.form.get("emd_amount") or 0),
                    float(request.form.get("fee_amount") or 0),
                    request.form.get("deadline", "").strip(),
                    request.form.get("source_url", "").strip(),
                    request.form.get("eligibility_notes", "").strip()
                ))

                tender_id = cursor.lastrowid
                default_documents = [
                    "PAN Card",
                    "GST Certificate",
                    "Firm Registration",
                    "Bank Details",
                    "ITR / Turnover Proof",
                    "Experience Certificate",
                    "Identity Proof",
                    "EMD Payment Proof"
                ]

                db.executemany("""
                    INSERT INTO tender_checklist
                    (tender_id, document_name, status)
                    VALUES (?, ?, 'Pending')
                """, [(tender_id, name) for name in default_documents])
            return redirect(url_for("business.tenders"))

    with connect() as db:
        rows = db.execute(
            "SELECT * FROM tenders ORDER BY id DESC LIMIT 100"
        ).fetchall()

    return render_template_string("""
    <!doctype html><html><head><title>Government Tenders</title>""" + STYLE + """</head>
    <body><div class="wrap">
    <h2>▤ Government Tender Management</h2>
    <p>Record tenders, deadlines, fees and eligibility information</p>
    {% if message %}<p>{{ message }}</p>{% endif %}
    <div class="card"><h3>Add Tender</h3>
      <form method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input name="title" placeholder="Tender title / work description" required>
        <input name="department" placeholder="Department / Government body">
        <input name="tender_reference" placeholder="Tender reference number">
        <input name="location" placeholder="Work location">
        <input name="estimated_value" type="number" min="0" step="0.01" placeholder="Estimated value (INR)">
        <input name="emd_amount" type="number" min="0" step="0.01" placeholder="EMD amount (INR)">
        <input name="fee_amount" type="number" min="0" step="0.01" placeholder="Tender fee (INR)">
        <label>Submission deadline</label>
        <input name="deadline" type="date">
        <input name="source_url" type="url" placeholder="Official tender URL">
        <textarea name="eligibility_notes" placeholder="Eligibility and document notes"></textarea>
        <button type="submit">Save Tender Record</button>
      </form>
    </div>
    <div class="card"><h3>Saved Tenders ({{ rows|length }})</h3>
    {% for t in rows %}
      <div class="item"><b>#{{ t.id }} — {{ t.title }}</b>
      <br>{{ t.department }} · Ref: {{ t.tender_reference }}
      <br>Location: {{ t.location }}
      <br>Value: ₹{{ t.estimated_value }} · EMD: ₹{{ t.emd_amount }} · Fee: ₹{{ t.fee_amount }}
      <br>Deadline: {{ t.deadline }} · Status: {{ t.status }}
      {% if t.source_url %}<br><a href="{{ t.source_url }}" target="_blank" rel="noopener">Official tender source</a>{% endif %}
      <br>Eligibility: {{ t.eligibility_notes }}</div>
    {% else %}<p>No tender records added yet.</p>{% endfor %}
    </div>
    <p><a href="/">← Back to Dashboard</a></p>
    </div></body></html>
    """, rows=rows, message=message)
