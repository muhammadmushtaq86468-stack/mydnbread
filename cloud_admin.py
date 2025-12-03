# cloud_admin.py
#
# GLOBAL COMMAND CENTER (DIRECT GITHUB)
#
# Upgrades:
# 1. Global Dashboard on Home Page (All Countries View).
# 2. Live Aggregated Stats (Total Cities, Files).
# 3. Premium White/Blue Professional UI.
# 4. No Local Storage Required.
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
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, render_template_string, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "global_command_key_secure"

# ---------------------------------------------------------
# LOAD CONFIG
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
# UI TEMPLATE (PREMIUM DASHBOARD)
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Domain Nexus | Command Center</title>
    
    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary: #0f172a;
            --accent: #3b82f6;
            --bg-body: #f1f5f9;
            --card-bg: #ffffff;
            --text-main: #334155;
        }
        
        body { background-color: var(--bg-body); color: var(--text-main); font-family: 'Plus Jakarta Sans', sans-serif; }
        
        /* Sidebar */
        .sidebar {
            width: 260px; position: fixed; top: 0; bottom: 0; left: 0;
            background: var(--primary); color: white; padding: 20px;
            overflow-y: auto; z-index: 1000;
            transition: all 0.3s;
        }
        .sidebar-header { font-size: 1.2rem; font-weight: 700; color: white; margin-bottom: 30px; display: flex; align-items: center; }
        .nav-link { color: #94a3b8; padding: 12px 15px; border-radius: 8px; font-weight: 500; margin-bottom: 5px; display: flex; align-items: center; }
        .nav-link:hover, .nav-link.active { background: rgba(255,255,255,0.1); color: white; }
        .nav-link i { margin-right: 12px; font-size: 1.1rem; }
        
        /* Main Content */
        .main-content { margin-left: 260px; padding: 30px; }
        
        /* Stat Cards */
        .stat-card {
            background: var(--card-bg); border: none; border-radius: 16px;
            padding: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            height: 100%; transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin-bottom: 15px; }
        .stat-value { font-size: 2rem; font-weight: 700; color: #0f172a; line-height: 1.2; }
        .stat-label { font-size: 0.875rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Tables */
        .card-table { background: white; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); overflow: hidden; border: none; }
        .table thead th { background: #f8fafc; color: #475569; font-weight: 600; padding: 18px 20px; border-bottom: 1px solid #e2e8f0; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }
        .table tbody td { padding: 16px 20px; vertical-align: middle; border-bottom: 1px solid #f1f5f9; color: #334155; font-weight: 500; }
        .table tr:last-child td { border-bottom: none; }
        .table tr:hover { background-color: #f8fafc; }
        
        /* Badges & Buttons */
        .btn-primary { background: var(--accent); border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; }
        .badge-soft { padding: 6px 12px; border-radius: 30px; font-size: 0.75rem; font-weight: 600; }
        .bg-blue-soft { background: #eff6ff; color: #2563eb; }
        .bg-green-soft { background: #dcfce7; color: #16a34a; }
        
        /* Responsive */
        @media (max-width: 992px) {
            .sidebar { transform: translateX(-100%); }
            .main-content { margin-left: 0; }
        }
    </style>
</head>
<body>

    <!-- SIDEBAR -->
    <div class="sidebar">
        <div class="sidebar-header">
            <i class="bi bi-hdd-network-fill me-2 text-primary" style="color: #60a5fa !important;"></i> DOMAIN NEXUS
        </div>
        
        <div class="nav flex-column">
            <a href="/" class="nav-link {{ 'active' if page == 'dashboard' }}">
                <i class="bi bi-grid-fill"></i> Global Overview
            </a>
            <div class="mt-4 mb-2 px-3 text-uppercase text-white-50" style="font-size: 0.75rem; font-weight: 700;">Quick Access</div>
            {% for c in countries %}
            <a href="/country/{{ c }}" class="nav-link {{ 'active' if selected_country == c }}">
                <i class="bi bi-folder"></i> {{ c }}
            </a>
            {% endfor %}
        </div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="main-content">
        
        <div class="d-flex justify-content-between align-items-center mb-5">
            <div>
                <h2 class="fw-bold m-0 text-dark">{{ title }}</h2>
                <p class="text-muted m-0">Real-time connection to GitHub Repository</p>
            </div>
            <div class="d-flex gap-2">
                <span class="badge bg-white text-success border px-3 py-2 d-flex align-items-center shadow-sm">
                    <i class="bi bi-circle-fill me-2" style="font-size: 8px;"></i> System Online
                </span>
                <a href="/" class="btn btn-white border shadow-sm text-dark"><i class="bi bi-arrow-clockwise"></i></a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} shadow-sm border-0 rounded-3 mb-4">
                        <i class="bi bi-info-circle-fill me-2"></i> {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- DYNAMIC CONTENT -->
        {{ CONTENT | safe }}
        
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ---------------------------------------------------------
# GITHUB API ENGINE
# ---------------------------------------------------------
def get_github_structure():
    """
    Scans the 'db/' folder and returns a structure of Countries & File Counts.
    Does NOT download DBs (Fast Scan).
    """
    structure = []
    total_cities = 0
    
    # 1. Get Countries (Folders)
    try:
        r = requests.get(f"{API_BASE}/db", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            items = r.json()
            countries = [i['name'] for i in items if i['type'] == 'dir']
            
            # 2. Get Cities count for each (Using threads for speed)
            def fetch_count(country):
                try:
                    c_r = requests.get(f"{API_BASE}/db/{country}", headers=HEADERS, timeout=10)
                    if c_r.status_code == 200:
                        files = [x for x in c_r.json() if x['name'].endswith('.sqlite')]
                        return {"name": country, "files": len(files)}
                except: return None
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(fetch_count, countries))
            
            # Filter None and sort
            structure = [r for r in results if r]
            total_cities = sum(x['files'] for x in structure)
            
    except: pass
    
    return structure, total_cities

def get_db_files(country):
    try:
        r = requests.get(f"{API_BASE}/db/{country}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return [i['name'] for i in r.json() if i['name'].endswith('.sqlite')]
    except: pass
    return []

def fetch_and_process_db(country, filename, action_callback):
    """Downloads DB to RAM, Edits, Pushes back."""
    api_url = f"{API_BASE}/db/{country}/{filename}"
    r = requests.get(api_url, headers=HEADERS)
    if r.status_code != 200: return None, "Fetch Failed"
    
    data = r.json()
    sha = data['sha']
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp.write(base64.b64decode(data['content']))
        tmp_path = tmp.name
        
    try:
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row
        res = action_callback(conn)
        
        if res == "SAVE":
            conn.close()
            with open(tmp_path, "rb") as f: content = f.read()
            push_data = {
                "message": f"Update {country}/{filename}",
                "content": base64.b64encode(content).decode('utf-8'),
                "sha": sha, "branch": GH_BRANCH
            }
            p = requests.put(api_url, headers=HEADERS, json=push_data)
            return (p.status_code in [200, 201]), "Saved"
            
        conn.close()
        return res, "Read OK"
    except Exception as e: return None, str(e)
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    # 1. Get Global Overview
    countries_data, total_cities = get_github_structure()
    countries_list = [c['name'] for c in countries_data]
    
    # Generate Table Rows
    rows_html = ""
    for idx, c in enumerate(countries_data, 1):
        rows_html += f"""
        <tr>
            <td style="width: 50px;">#{idx}</td>
            <td>
                <div class="fw-bold text-dark">{c['name']}</div>
                <div class="small text-muted">Active Region</div>
            </td>
            <td>
                <span class="badge bg-blue-soft text-primary fs-6">{c['files']} Cities</span>
            </td>
            <td>
                <div class="progress" style="height: 6px; width: 100px;">
                    <div class="progress-bar bg-primary" role="progressbar" style="width: 100%"></div>
                </div>
            </td>
            <td class="text-end">
                <a href="/country/{c['name']}" class="btn btn-sm btn-outline-primary rounded-pill px-3">View Cities <i class="bi bi-arrow-right ms-1"></i></a>
            </td>
        </tr>
        """

    content = f"""
    <!-- TOP STATS -->
    <div class="row g-4 mb-5">
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-icon bg-blue-soft text-primary"><i class="bi bi-globe"></i></div>
                <div class="stat-label">Active Countries</div>
                <div class="stat-value">{len(countries_data)}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-icon bg-green-soft text-success"><i class="bi bi-building"></i></div>
                <div class="stat-label">Total Cities</div>
                <div class="stat-value">{total_cities}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-icon" style="background:#fef3c7; color:#d97706"><i class="bi bi-hdd-stack"></i></div>
                <div class="stat-label">Database Files</div>
                <div class="stat-value">{total_cities}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-icon" style="background:#f3e8ff; color:#7e22ce"><i class="bi bi-cpu"></i></div>
                <div class="stat-label">System Status</div>
                <div class="stat-value text-success fs-4 mt-2">Operational</div>
            </div>
        </div>
    </div>

    <!-- MAIN TABLE -->
    <div class="card-table">
        <div class="p-4 border-bottom bg-white d-flex justify-content-between align-items-center">
            <h5 class="fw-bold m-0 text-dark"><i class="bi bi-list-stars me-2 text-primary"></i>Global Coverage</h5>
            <span class="badge bg-light text-dark border">Live Data</span>
        </div>
        <table class="table mb-0">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Country Name</th>
                    <th>Database Volume</th>
                    <th>Health</th>
                    <th class="text-end">Action</th>
                </tr>
            </thead>
            <tbody>
                {rows_html if rows_html else '<tr><td colspan="5" class="text-center py-5 text-muted">No data found on GitHub. Run the Extractor.</td></tr>'}
            </tbody>
        </table>
    </div>
    """
    
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries_list, page='dashboard', title="Command Center", selected_country="")

@app.route('/country/<country>')
def view_country(country):
    countries_list = [c['name'] for c in get_github_structure()[0]]
    cities = get_db_files(country)
    
    cards = ""
    for c in cities:
        name = c.replace(".sqlite", "")
        cards += f"""
        <div class="col-md-4 mb-4">
            <div class="stat-card border h-100 d-flex flex-column">
                <div class="d-flex justify-content-between mb-3">
                    <div class="stat-icon bg-light text-dark mb-0 fs-5" style="width:40px;height:40px;"><i class="bi bi-database-fill"></i></div>
                    <span class="badge bg-success-soft text-success align-self-start">Active</span>
                </div>
                <h5 class="fw-bold text-dark">{name}</h5>
                <p class="text-muted small mb-4">Database file for {name}, {country}</p>
                <a href="/manage/{country}/{c}" class="btn btn-primary w-100 mt-auto">Access Database</a>
            </div>
        </div>
        """
        
    content = f"<div class='row'>{cards}</div>" if cities else "<p>No cities found.</p>"
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries_list, page='country', title=country, selected_country=country)

@app.route('/manage/<country>/<filename>')
def manage_db(country, filename):
    countries_list = [c['name'] for c in get_github_structure()[0]]
    
    def get_data(conn):
        c = conn.cursor()
        # Stats
        c.execute("SELECT status, count(*) FROM domains GROUP BY status")
        stats = {"total":0, "pending":0, "success":0, "failed":0}
        for s, count in c.fetchall(): stats[s] = count
        stats["total"] = sum(stats.values())
        
        # Rows
        c.execute("SELECT * FROM domains ORDER BY id DESC LIMIT 100")
        rows = [dict(r) for r in c.fetchall()]
        return {"stats": stats, "rows": rows}

    data, msg = fetch_and_process_db(country, filename, get_data)
    if not data:
        flash(f"Error: {msg}", "danger")
        return redirect("/")
        
    stats = data['stats']
    rows_html = ""
    for r in data['rows']:
        st_cls = "bg-warning text-dark bg-opacity-25" if r['status']=='pending' else ("bg-success text-success bg-opacity-10" if r['status']=='success' else "bg-danger text-danger bg-opacity-10")
        rows_html += f"""
        <tr>
            <td>#{r['id']}</td>
            <td><span class="fw-bold">{r['domain']}</span><br><small class="text-muted">{r['niche']}</small></td>
            <td><span class="badge {st_cls} px-2 py-1">{r['status'].upper()}</span></td>
            <td>
                <a href="/edit/{country}/{filename}/{r['id']}/success" class="btn btn-sm btn-light border"><i class="bi bi-check text-success"></i></a>
                <a href="/edit/{country}/{filename}/{r['id']}/failed" class="btn btn-sm btn-light border"><i class="bi bi-x text-danger"></i></a>
            </td>
        </tr>
        """

    content = f"""
    <div class="row g-3 mb-4">
        <div class="col-md-3"><div class="stat-card"><div class="stat-label">Total Records</div><div class="stat-value">{stats['total']}</div></div></div>
        <div class="col-md-3"><div class="stat-card"><div class="stat-label text-primary">Pending</div><div class="stat-value text-primary">{stats['pending']}</div></div></div>
        <div class="col-md-3"><div class="stat-card"><div class="stat-label text-success">Success</div><div class="stat-value text-success">{stats['success']}</div></div></div>
        <div class="col-md-3"><div class="stat-card"><div class="stat-label text-danger">Failed</div><div class="stat-value text-danger">{stats['failed']}</div></div></div>
    </div>
    
    <div class="card p-3 mb-4 border-0 shadow-sm" style="background: #f8fafc;">
        <form action="/bulk/{country}/{filename}" method="POST" class="row g-2">
            <div class="col-md-4"><select name="target" class="form-select"><option value="failed">Failed Domains</option><option value="pending">Pending</option></select></div>
            <div class="col-md-4"><select name="action" class="form-select"><option value="pending">Reset to Pending</option><option value="delete">Delete</option></select></div>
            <div class="col-md-4"><button class="btn btn-dark w-100">Run Bulk Action</button></div>
        </form>
    </div>

    <div class="card-table">
        <table class="table mb-0"><thead><tr><th>ID</th><th>Domain</th><th>Status</th><th>Actions</th></tr></thead><tbody>{rows_html}</tbody></table>
    </div>
    """
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries_list, page='manage', title=filename.replace(".sqlite",""), selected_country=country)

@app.route('/edit/<c>/<f>/<id>/<st>')
def edit_row(c, f, id, st):
    def update(conn):
        conn.execute("UPDATE domains SET status=?, updated_at=? WHERE id=?", (st, int(time.time()), id))
        conn.commit()
        return "SAVE"
    fetch_and_process_db(c, f, update)
    return redirect(url_for('manage_db', country=c, filename=f))

@app.route('/bulk/<c>/<f>', methods=['POST'])
def bulk_op(c, f):
    t, a = request.form.get('target'), request.form.get('action')
    def op(conn):
        if a == 'delete': conn.execute("DELETE FROM domains WHERE status=?", (t,))
        else: conn.execute("UPDATE domains SET status=? WHERE status=?", (a, t))
        conn.commit()
        return "SAVE"
    fetch_and_process_db(c, f, op)
    return redirect(url_for('manage_db', country=c, filename=f))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
