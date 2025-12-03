# cloud_admin.py
#
# DIRECT GITHUB DATABASE EDITOR (NO LOCAL FILES)
#
# Features:
# 1. Edits GitHub SQLite files directly in-memory (Transient).
# 2. No manual download/upload buttons.
# 3. Real-Time Analytics from GitHub.
# 4. Professional Responsive White Theme.
#
# USAGE:
# python cloud_admin.py

import os
import sqlite3
import json
import time
import base64
import requests
import tempfile
from flask import Flask, request, render_template_string, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "live_cloud_key_secure"

# ---------------------------------------------------------
# LOAD CONFIG (Only for API Credentials)
# ---------------------------------------------------------
if not os.path.exists("config.json"):
    print("CRITICAL: config.json not found!")
    exit()

with open("config.json", "r", encoding="utf-8") as f:
    CFG = json.load(f)
    GH_USER = CFG["GITHUB"]["USER"]
    GH_REPO = CFG["GITHUB"]["REPO"]
    GH_BRANCH = CFG["GITHUB"]["BRANCH"]
    GH_PAT = CFG["GITHUB"]["PAT"]

API_BASE = f"https://api.github.com/repos/{GH_USER}/{GH_REPO}/contents"
HEADERS = {"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}

# ---------------------------------------------------------
# HTML TEMPLATE (PREMIUM WHITE UI - RESPONSIVE)
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Live Cloud DB | Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        body { background-color: #f8fafc; font-family: 'Inter', sans-serif; color: #334155; }
        
        .navbar { background: white; border-bottom: 1px solid #e2e8f0; padding: 1rem 0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .navbar-brand { font-weight: 700; color: #2563eb !important; letter-spacing: -0.5px; font-size: 1.5rem; }
        
        .card { border: none; border-radius: 12px; background: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: transform 0.2s; }
        .card:hover { transform: translateY(-2px); }
        
        .stat-label { font-size: 0.875rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-val { font-size: 2rem; font-weight: 700; color: #0f172a; margin-top: 0.5rem; }
        
        .table-container { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .table thead th { background: #f1f5f9; color: #475569; font-weight: 600; padding: 1rem; border: none; }
        .table tbody td { padding: 1rem; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
        
        .badge-status { padding: 0.35em 0.65em; font-size: 0.75em; font-weight: 600; border-radius: 0.25rem; }
        .bg-pending { background-color: #e0f2fe; color: #0284c7; }
        .bg-success-custom { background-color: #dcfce7; color: #16a34a; }
        .bg-failed-custom { background-color: #fee2e2; color: #dc2626; }
        
        .sidebar { position: fixed; top: 0; bottom: 0; left: 0; width: 280px; padding: 20px; background: white; border-right: 1px solid #e2e8f0; overflow-y: auto; z-index: 1000; }
        .main-content { margin-left: 280px; padding: 30px; }
        
        @media (max-width: 768px) {
            .sidebar { position: relative; width: 100%; height: auto; border-right: none; border-bottom: 1px solid #e2e8f0; }
            .main-content { margin-left: 0; }
        }
        
        .nav-link { color: #475569; font-weight: 500; padding: 10px 15px; border-radius: 8px; margin-bottom: 4px; }
        .nav-link:hover, .nav-link.active { background-color: #eff6ff; color: #2563eb; }
        .nav-link i { margin-right: 10px; opacity: 0.8; }
    </style>
</head>
<body>

    <!-- SIDEBAR -->
    <div class="sidebar">
        <div class="d-flex align-items-center mb-4 px-2">
            <i class="bi bi-cloud-lightning-fill text-primary fs-3 me-2"></i>
            <span class="fw-bold fs-4 text-dark">LiveDB</span>
        </div>
        
        <h6 class="text-uppercase text-muted small fw-bold px-2 mb-3">Countries (GitHub)</h6>
        <div class="nav flex-column">
            {% if countries %}
                {% for c in countries %}
                <a href="/country/{{ c }}" class="nav-link {{ 'active' if selected_country == c }}">
                    <i class="bi bi-globe"></i> {{ c }}
                </a>
                {% endfor %}
            {% else %}
                <div class="px-2 text-danger small">No Data found on GitHub</div>
            {% endif %}
        </div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="main-content">
        
        <!-- HEADER -->
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 class="fw-bold m-0">{{ title }}</h2>
                <p class="text-muted m-0">{{ subtitle }}</p>
            </div>
            <div>
                <span class="badge bg-white text-success border px-3 py-2">
                    <i class="bi bi-wifi"></i> Live Connected
                </span>
            </div>
        </div>

        <!-- FLASH MESSAGES -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} shadow-sm border-0 rounded-3 mb-4">
                        <i class="bi bi-info-circle-fill me-2"></i> {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- INJECTED CONTENT -->
        {{ CONTENT | safe }}
        
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ---------------------------------------------------------
# DIRECT GITHUB API FUNCTIONS (NO LOCAL SYNC)
# ---------------------------------------------------------
def get_github_countries():
    """Lists folders in 'db/' directly from GitHub."""
    try:
        r = requests.get(f"{API_BASE}/db", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return [i['name'] for i in r.json() if i['type'] == 'dir']
        return []
    except: return []

def get_github_cities(country):
    """Lists .sqlite files in a country folder."""
    try:
        r = requests.get(f"{API_BASE}/db/{country}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return [i['name'] for i in r.json() if i['name'].endswith('.sqlite')]
        return []
    except: return []

def fetch_and_process_db(country, filename, action_callback):
    """
    1. Downloads DB to RAM/Temp.
    2. Runs the 'action_callback' (SQL queries).
    3. If modified, Pushes back to GitHub immediately.
    """
    api_url = f"{API_BASE}/db/{country}/{filename}"
    
    # 1. Fetch File
    r = requests.get(api_url, headers=HEADERS)
    if r.status_code != 200:
        return None, "Failed to fetch file from GitHub"
        
    file_data = r.json()
    sha = file_data['sha']
    content_b64 = file_data['content']
    
    # Write to Temp File (Needed for SQLite driver)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp.write(base64.b64decode(content_b64))
        tmp_path = tmp.name
        
    try:
        # 2. Perform Action (Read/Write)
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row
        result = action_callback(conn)
        
        # If action returned "SAVE", we push back
        if result == "SAVE":
            conn.close() # Close to flush
            
            with open(tmp_path, "rb") as f:
                new_content = f.read()
            
            new_b64 = base64.b64encode(new_content).decode("utf-8")
            
            push_data = {
                "message": f"Cloud Admin Update: {country}/{filename}",
                "content": new_b64,
                "sha": sha,
                "branch": GH_BRANCH
            }
            
            p = requests.put(api_url, headers=HEADERS, json=push_data)
            if p.status_code in [200, 201]:
                return True, "Updated successfully on GitHub"
            else:
                return False, f"GitHub Push Failed: {p.status_code}"
                
        conn.close()
        return result, "Read Success" # Return data if read-only
        
    except Exception as e:
        return None, str(e)
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    countries = get_github_countries()
    content = """
    <div class="text-center py-5">
        <div class="mb-4">
            <i class="bi bi-cloud-check display-1 text-primary"></i>
        </div>
        <h2 class="fw-bold">Connected to GitHub Database</h2>
        <p class="text-muted">Select a country from the sidebar to manage live data.</p>
    </div>
    """
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries, title="Dashboard", subtitle="Overview", selected_country="")

@app.route('/country/<country>')
def view_country(country):
    countries = get_github_countries()
    cities = get_github_cities(country)
    
    city_cards = ""
    for c_file in cities:
        city_name = c_file.replace(".sqlite", "")
        city_cards += f"""
        <div class="col-md-4 mb-4">
            <div class="card h-100">
                <div class="card-body d-flex flex-column justify-content-between">
                    <div>
                        <h5 class="fw-bold mb-1">{city_name}</h5>
                        <small class="text-muted">{country}</small>
                    </div>
                    <div class="mt-4">
                        <a href="/manage/{country}/{c_file}" class="btn btn-outline-primary w-100 fw-bold">
                            Open Database <i class="bi bi-arrow-right ms-2"></i>
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
        
    content = f"<div class='row'>{city_cards}</div>" if cities else "<p class='text-muted'>No cities found.</p>"
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries, title=country, subtitle="Select a City Database", selected_country=country)

@app.route('/manage/<country>/<filename>')
def manage_db(country, filename):
    countries = get_github_countries()
    city_name = filename.replace(".sqlite", "")
    
    # DEFINE READ ACTION
    def read_stats(conn):
        c = conn.cursor()
        stats = {"total":0, "pending":0, "success":0, "failed":0}
        
        # Get Stats
        c.execute("SELECT status, count(*) FROM domains GROUP BY status")
        for row in c.fetchall():
            stats[row[0]] = row[1]
            stats["total"] += row[1]
            
        # Get Recent Rows
        c.execute("SELECT * FROM domains ORDER BY id DESC LIMIT 100")
        rows = [dict(row) for row in c.fetchall()]
        
        return {"stats": stats, "rows": rows}

    # EXECUTE
    data, msg = fetch_and_process_db(country, filename, read_stats)
    
    if not data:
        flash(f"Error loading DB: {msg}", "danger")
        return redirect(f"/country/{country}")
        
    stats = data['stats']
    rows = data['rows']
    
    # BUILD TABLE
    table_rows = ""
    for r in rows:
        st_badge = "bg-secondary"
        if r['status'] == 'success': st_badge = "bg-success-custom"
        elif r['status'] == 'failed': st_badge = "bg-failed-custom"
        elif r['status'] == 'pending': st_badge = "bg-pending"
        
        table_rows += f"""
        <tr>
            <td>{r['id']}</td>
            <td><a href="http://{r['domain']}" target="_blank" class="text-decoration-none fw-bold text-dark">{r['domain']}</a></td>
            <td><span class="badge-status {st_badge}">{r['status'].upper()}</span></td>
            <td>
                <a href="/update/{country}/{filename}/{r['id']}/success" class="btn btn-sm btn-light text-success border"><i class="bi bi-check-lg"></i></a>
                <a href="/update/{country}/{filename}/{r['id']}/failed" class="btn btn-sm btn-light text-danger border"><i class="bi bi-x-lg"></i></a>
            </td>
        </tr>
        """

    content = f"""
    <!-- STATS CARDS -->
    <div class="row g-3 mb-4">
        <div class="col-md-3"><div class="card p-3"><div class="stat-label">Total</div><div class="stat-val">{stats['total']}</div></div></div>
        <div class="col-md-3"><div class="card p-3"><div class="stat-label text-primary">Pending</div><div class="stat-val text-primary">{stats['pending']}</div></div></div>
        <div class="col-md-3"><div class="card p-3"><div class="stat-label text-success">Success</div><div class="stat-val text-success">{stats['success']}</div></div></div>
        <div class="col-md-3"><div class="card p-3"><div class="stat-label text-danger">Failed</div><div class="stat-val text-danger">{stats['failed']}</div></div></div>
    </div>

    <!-- BULK ACTIONS -->
    <div class="card p-4 mb-4 border-0 shadow-sm" style="background: #eff6ff;">
        <h6 class="fw-bold text-primary mb-3"><i class="bi bi-tools"></i> REMOTE ACTIONS</h6>
        <form action="/bulk_update/{country}/{filename}" method="POST" class="row g-2 align-items-end">
            <div class="col-md-4">
                <label class="small fw-bold text-muted">TARGET</label>
                <select name="target" class="form-select border-0"><option value="failed">Failed Domains</option><option value="pending">Pending Domains</option></select>
            </div>
            <div class="col-md-4">
                <label class="small fw-bold text-muted">ACTION</label>
                <select name="action" class="form-select border-0"><option value="pending">Reset to Pending</option><option value="delete">Delete Forever</option></select>
            </div>
            <div class="col-md-4">
                <button type="submit" class="btn btn-primary w-100 fw-bold">EXECUTE ON GITHUB</button>
            </div>
        </form>
    </div>

    <!-- DATA TABLE -->
    <div class="table-container">
        <table class="table mb-0">
            <thead><tr><th>ID</th><th>Domain</th><th>Status</th><th>Quick Edit</th></tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
    </div>
    """
    
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries, title=city_name, subtitle="Live Database Manager", selected_country=country)

@app.route('/update/<country>/<filename>/<id>/<status>')
def update_row(country, filename, id, status):
    def db_action(conn):
        conn.execute("UPDATE domains SET status=?, updated_at=? WHERE id=?", (status, int(time.time()), id))
        conn.commit()
        return "SAVE" # Triggers Push
    
    success, msg = fetch_and_process_db(country, filename, db_action)
    if success: flash(f"Updated ID {id} on GitHub!", "success")
    else: flash(f"Update Failed: {msg}", "danger")
    
    return redirect(url_for('manage_db', country=country, filename=filename))

@app.route('/bulk_update/<country>/<filename>', methods=['POST'])
def bulk_update(country, filename):
    target = request.form.get('target')
    action = request.form.get('action')
    
    def db_action(conn):
        if action == "delete":
            conn.execute("DELETE FROM domains WHERE status=?", (target,))
        else:
            conn.execute("UPDATE domains SET status=?, updated_at=? WHERE status=?", (action, int(time.time()), target))
        conn.commit()
        return "SAVE" # Triggers Push
        
    success, msg = fetch_and_process_db(country, filename, db_action)
    if success: flash("Bulk Action Synced to GitHub!", "success")
    else: flash(f"Bulk Failed: {msg}", "danger")
    
    return redirect(url_for('manage_db', country=country, filename=filename))

# ---------------------------------------------------------
# RUNNER
# ---------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*50)
    print(" ☁️  CLOUD DB MANAGER STARTED")
    print(" 🔗  Open: http://localhost:5000")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
