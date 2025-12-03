# cloud_admin.py
#
# ULTIMATE CLOUD DASHBOARD (GITHUB DIRECT)
#
# Features:
# 1. LIVE VELOCITY METRICS (1m, 5m, 1h, 24h).
# 2. GLOBAL AGGREGATED STATS (Success, Pending, Failed).
# 3. MULTI-THREADED SCANNER (For fast Dashboard loading).
# 4. PREMIUM UI (Charts, Cards, Responsive).
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, render_template_string, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "ultimate_admin_key_secure"

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
# UI TEMPLATE (PREMIUM DASHBOARD WITH CHARTS)
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Domain Nexus | Ultimate Dashboard</title>
    
    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        :root {
            --primary: #4f46e5;
            --secondary: #64748b;
            --success: #10b981;
            --danger: #ef4444;
            --bg-body: #f8fafc;
            --card-bg: #ffffff;
            --sidebar-bg: #1e1b4b;
        }
        
        body { background-color: var(--bg-body); font-family: 'Outfit', sans-serif; color: #334155; }
        
        /* Sidebar */
        .sidebar {
            width: 260px; position: fixed; top: 0; bottom: 0; left: 0;
            background: var(--sidebar-bg); color: white; padding: 20px;
            overflow-y: auto; z-index: 1000;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1);
        }
        .sidebar-header { font-size: 1.4rem; font-weight: 700; color: white; margin-bottom: 40px; display: flex; align-items: center; }
        .nav-link { color: #cbd5e1; padding: 12px 15px; border-radius: 10px; font-weight: 500; margin-bottom: 8px; transition: all 0.2s; }
        .nav-link:hover, .nav-link.active { background: rgba(255,255,255,0.1); color: white; transform: translateX(5px); }
        .nav-link i { margin-right: 12px; width: 20px; text-align: center; }
        
        /* Main Content */
        .main-content { margin-left: 260px; padding: 30px; }
        
        /* Stats Cards - Velocity */
        .velocity-card {
            background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%);
            color: white; border-radius: 16px; padding: 20px;
            box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
            border: none; position: relative; overflow: hidden;
        }
        .velocity-card::before {
            content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            transform: rotate(45deg);
        }
        
        /* General Stats */
        .stat-card {
            background: white; border-radius: 16px; padding: 25px; border: none;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); height: 100%;
            border-bottom: 4px solid transparent;
        }
        .stat-card.success { border-bottom-color: var(--success); }
        .stat-card.failed { border-bottom-color: var(--danger); }
        .stat-card.pending { border-bottom-color: var(--primary); }
        
        .stat-val { font-size: 2.5rem; font-weight: 700; color: #0f172a; line-height: 1; margin: 10px 0; }
        .stat-label { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px; }
        
        /* Table */
        .table-card { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .table thead th { background: #f1f5f9; padding: 15px 20px; font-weight: 600; color: #64748b; font-size: 0.8rem; text-transform: uppercase; }
        .table tbody td { padding: 15px 20px; vertical-align: middle; border-bottom: 1px solid #f1f5f9; }
        
        /* Badges */
        .badge-soft { padding: 6px 12px; border-radius: 8px; font-weight: 600; font-size: 0.75rem; }
        .bg-pending { background: #e0f2fe; color: #0369a1; }
        .bg-success { background: #dcfce7; color: #15803d; }
        .bg-failed { background: #fee2e2; color: #b91c1c; }

        @media (max-width: 992px) {
            .sidebar { width: 0; padding: 0; overflow: hidden; }
            .main-content { margin-left: 0; }
        }
    </style>
</head>
<body>

    <!-- SIDEBAR -->
    <div class="sidebar">
        <div class="sidebar-header">
            <i class="bi bi-hdd-network me-2 text-info"></i> NEXUS DB
        </div>
        
        <div class="nav flex-column">
            <a href="/" class="nav-link {{ 'active' if page == 'dashboard' }}">
                <i class="bi bi-speedometer2"></i> Global Dashboard
            </a>
            <div class="mt-4 mb-2 px-3 text-uppercase text-white-50" style="font-size: 0.7rem; font-weight: 700;">Countries</div>
            {% for c in countries %}
            <a href="/country/{{ c }}" class="nav-link {{ 'active' if selected_country == c }}">
                <i class="bi bi-geo-alt-fill"></i> {{ c }}
            </a>
            {% endfor %}
        </div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="main-content">
        
        <div class="d-flex justify-content-between align-items-center mb-5">
            <div>
                <h2 class="fw-bold m-0 text-dark">{{ title }}</h2>
                <p class="text-muted m-0">Live GitHub Connection • <span class="text-success fw-bold">● Online</span></p>
            </div>
            <a href="/" class="btn btn-primary shadow-sm"><i class="bi bi-arrow-clockwise me-2"></i> Refresh Data</a>
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

        {{ CONTENT | safe }}
        
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ---------------------------------------------------------
# GITHUB & ANALYTICS ENGINE (MULTI-THREADED)
# ---------------------------------------------------------
def get_folders():
    try:
        r = requests.get(f"{API_BASE}/db", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return [i['name'] for i in r.json() if i['type'] == 'dir']
    except: pass
    return []

def get_files_in_country(country):
    try:
        r = requests.get(f"{API_BASE}/db/{country}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return [i for i in r.json() if i['name'].endswith('.sqlite')]
    except: pass
    return []

def scan_single_db(file_info):
    """
    Downloads a single DB to RAM, queries stats, and returns them.
    Used by ThreadPool for parallel scanning.
    """
    stats = {
        "total": 0, "pending": 0, "success": 0, "failed": 0,
        "m1": 0, "m5": 0, "h1": 0, "h24": 0, "country": "Unknown"
    }
    
    try:
        # Download
        r = requests.get(file_info['download_url'], timeout=20)
        if r.status_code != 200: return stats
        
        # Temp File
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
            tmp.write(r.content)
            tmp_path = tmp.name
            
        # Query
        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()
        
        # 1. Totals
        c.execute("SELECT status, count(*) FROM domains GROUP BY status")
        for s, count in c.fetchall():
            stats[s] = count
            stats["total"] += count
            
        # 2. Velocity (Time based)
        now = int(time.time())
        c.execute("SELECT count(*) FROM domains WHERE updated_at >= ?", (now - 60,))
        stats["m1"] = c.fetchone()[0]
        
        c.execute("SELECT count(*) FROM domains WHERE updated_at >= ?", (now - 300,))
        stats["m5"] = c.fetchone()[0]
        
        c.execute("SELECT count(*) FROM domains WHERE updated_at >= ?", (now - 3600,))
        stats["h1"] = c.fetchone()[0]
        
        c.execute("SELECT count(*) FROM domains WHERE updated_at >= ?", (now - 86400,))
        stats["h24"] = c.fetchone()[0]
        
        conn.close()
        os.remove(tmp_path)
        
    except Exception as e:
        # print(f"Scan error: {e}")
        pass
        
    return stats

def get_global_analytics():
    """
    Scans ALL databases in ALL countries using Threads.
    Returns aggregated data for the Dashboard.
    """
    countries = get_folders()
    all_files = []
    
    # 1. Collect all file URLs first
    for c in countries:
        files = get_files_in_country(c)
        for f in files:
            f['country_name'] = c # Tag with country
            all_files.append(f)
            
    # 2. Parallel Scan (Limit 20 threads to be safe with API/Memory)
    global_stats = {
        "total": 0, "pending": 0, "success": 0, "failed": 0,
        "m1": 0, "m5": 0, "h1": 0, "h24": 0,
        "cities_count": len(all_files)
    }
    
    country_breakdown = {}
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(scan_single_db, f): f for f in all_files}
        
        for future in as_completed(futures):
            f_info = futures[future]
            data = future.result()
            c_name = f_info['country_name']
            
            # Aggregate Global
            global_stats["total"] += data["total"]
            global_stats["pending"] += data["pending"]
            global_stats["success"] += data["success"]
            global_stats["failed"] += data["failed"]
            global_stats["m1"] += data["m1"]
            global_stats["m5"] += data["m5"]
            global_stats["h1"] += data["h1"]
            global_stats["h24"] += data["h24"]
            
            # Aggregate Country
            if c_name not in country_breakdown:
                country_breakdown[c_name] = {"total": 0, "success": 0}
            country_breakdown[c_name]["total"] += data["total"]
            country_breakdown[c_name]["success"] += data["success"]
            
    return global_stats, countries, country_breakdown

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    # Heavy operation - Scans everything
    stats, countries_list, c_breakdown = get_global_analytics()
    
    # Generate Chart Data string
    chart_labels = list(c_breakdown.keys())
    chart_data = [v['total'] for v in c_breakdown.values()]
    
    content = f"""
    <!-- VELOCITY SECTION -->
    <div class="row g-4 mb-5">
        <div class="col-12">
            <div class="velocity-card">
                <div class="row align-items-center">
                    <div class="col-md-3 border-end border-white border-opacity-25 text-center">
                        <div class="text-white-50 text-uppercase small fw-bold">Last 1 Minute</div>
                        <div class="display-4 fw-bold">{stats['m1']}</div>
                        <div class="small">New Domains</div>
                    </div>
                    <div class="col-md-3 border-end border-white border-opacity-25 text-center">
                        <div class="text-white-50 text-uppercase small fw-bold">Last 5 Minutes</div>
                        <div class="display-4 fw-bold">{stats['m5']}</div>
                        <div class="small">New Domains</div>
                    </div>
                    <div class="col-md-3 border-end border-white border-opacity-25 text-center">
                        <div class="text-white-50 text-uppercase small fw-bold">Last 1 Hour</div>
                        <div class="display-4 fw-bold">{stats['h1']}</div>
                        <div class="small">New Domains</div>
                    </div>
                    <div class="col-md-3 text-center">
                        <div class="text-white-50 text-uppercase small fw-bold">Last 24 Hours</div>
                        <div class="display-4 fw-bold">{stats['h24']}</div>
                        <div class="small">New Domains</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- OVERALL STATS -->
    <div class="row g-4 mb-5">
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-label">Total Extracted</div>
                <div class="stat-val">{stats['total']:,}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card pending">
                <div class="stat-label text-primary">Pending</div>
                <div class="stat-val text-primary">{stats['pending']:,}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card success">
                <div class="stat-label text-success">Success</div>
                <div class="stat-val text-success">{stats['success']:,}</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card failed">
                <div class="stat-label text-danger">Failed</div>
                <div class="stat-val text-danger">{stats['failed']:,}</div>
            </div>
        </div>
    </div>

    <!-- CHARTS & TABLES -->
    <div class="row g-4">
        <div class="col-md-8">
            <div class="table-card h-100">
                <div class="p-4 border-bottom bg-white d-flex justify-content-between align-items-center">
                    <h6 class="fw-bold m-0 text-dark">Top Performing Countries</h6>
                </div>
                <table class="table mb-0">
                    <thead><tr><th>Country</th><th>Total Domains</th><th>Success Rate</th><th>Action</th></tr></thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td class="fw-bold">{c}</td>
                            <td>{d['total']}</td>
                            <td><span class="badge bg-success">{round((d['success']/(d['total'] or 1))*100)}%</span></td>
                            <td><a href="/country/{c}" class="btn btn-sm btn-outline-primary">View</a></td>
                        </tr>
                        ''' for c, d in c_breakdown.items()])}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card">
                <h6 class="fw-bold mb-4">Database Health</h6>
                <canvas id="statusChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('statusChart');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: ['Success', 'Pending', 'Failed'],
                datasets: [{{
                    data: [{stats['success']}, {stats['pending']}, {stats['failed']}],
                    backgroundColor: ['#10b981', '#3b82f6', '#ef4444'],
                    borderWidth: 0
                }}]
            }},
            options: {{ responsive: true, cutout: '70%' }}
        }});
    </script>
    """
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries_list, page='dashboard', title="Global Command Center", selected_country="")

@app.route('/country/<country>')
def view_country(country):
    countries = get_folders()
    cities = get_files_in_country(country)
    
    cards = ""
    if not cities: cards = "<p class='p-4'>No data found.</p>"
    
    for c in cities:
        name = c['name'].replace(".sqlite", "")
        cards += f"""
        <div class="col-md-4 mb-4">
            <div class="stat-card border h-100 d-flex flex-column justify-content-between">
                <div>
                    <h5 class="fw-bold text-dark">{name}</h5>
                    <p class="text-muted small">Database File</p>
                </div>
                <a href="/manage/{country}/{c['name']}" class="btn btn-primary w-100 mt-3">Manage Database</a>
            </div>
        </div>
        """
    content = f"<div class='row'>{cards}</div>"
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=countries, page='country', title=country, selected_country=country)

@app.route('/manage/<country>/<filename>')
def manage_db(country, filename):
    def get_data(conn):
        c = conn.cursor()
        c.execute("SELECT status, count(*) FROM domains GROUP BY status")
        stats = {"total":0, "pending":0, "success":0, "failed":0}
        for s, count in c.fetchall(): stats[s] = count
        stats["total"] = sum(stats.values())
        c.execute("SELECT * FROM domains ORDER BY id DESC LIMIT 100")
        return {"stats": stats, "rows": [dict(r) for r in c.fetchall()]}

    res, msg = fetch_and_edit_db(country, filename, get_data)
    if not res: return f"Error: {msg}"
    
    stats = res['stats']
    rows_html = ""
    for r in res['rows']:
        st_cls = "bg-success" if r['status']=='success' else ("bg-danger" if r['status']=='failed' else "bg-pending")
        rows_html += f"""
        <tr>
            <td>#{r['id']}</td>
            <td><a href="http://{r['domain']}" target="_blank" class="fw-bold text-decoration-none">{r['domain']}</a></td>
            <td><span class="badge {st_cls}">{r['status']}</span></td>
            <td>
                <a href="/update/{country}/{filename}/{r['id']}/success" class="btn btn-sm btn-outline-success"><i class="bi bi-check"></i></a>
                <a href="/update/{country}/{filename}/{r['id']}/failed" class="btn btn-sm btn-outline-danger"><i class="bi bi-x"></i></a>
            </td>
        </tr>"""

    content = f"""
    <div class="row g-4 mb-4">
        <div class="col-md-3"><div class="stat-card"><div class="stat-label">Total</div><div class="stat-val">{stats['total']}</div></div></div>
        <div class="col-md-3"><div class="stat-card pending"><div class="stat-label text-primary">Pending</div><div class="stat-val text-primary">{stats['pending']}</div></div></div>
        <div class="col-md-3"><div class="stat-card success"><div class="stat-label text-success">Success</div><div class="stat-val text-success">{stats['success']}</div></div></div>
        <div class="col-md-3"><div class="stat-card failed"><div class="stat-label text-danger">Failed</div><div class="stat-val text-danger">{stats['failed']}</div></div></div>
    </div>
    
    <div class="card p-4 border-0 shadow-sm mb-4">
        <h6 class="fw-bold mb-3">BULK ACTIONS</h6>
        <form action="/bulk_action/{country}/{filename}" method="POST" class="row g-2">
            <div class="col-md-4"><select name="target" class="form-select"><option value="failed">Failed Domains</option><option value="pending">Pending</option></select></div>
            <div class="col-md-4"><select name="action" class="form-select"><option value="pending">Reset Status</option><option value="delete">Delete</option></select></div>
            <div class="col-md-4"><button class="btn btn-dark w-100">Execute</button></div>
        </form>
    </div>

    <div class="table-card"><table class="table mb-0"><thead><tr><th>ID</th><th>Domain</th><th>Status</th><th>Edit</th></tr></thead><tbody>{rows_html}</tbody></table></div>
    """
    return render_template_string(HTML_TEMPLATE, CONTENT=content, countries=get_folders(), page='manage', title=filename, selected_country=country)

# DB Helper
def fetch_and_edit_db(country, filename, callback):
    url = f"{API_BASE}/db/{country}/{filename}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200: return None, "Fetch Failed"
    data = r.json()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp.write(base64.b64decode(data['content']))
        tmp_path = tmp.name
        
    try:
        conn = sqlite3.connect(tmp_path)
        conn.row_factory = sqlite3.Row
        res = callback(conn)
        
        if res == "SAVE":
            conn.close()
            with open(tmp_path, "rb") as f: content = f.read()
            push = {
                "message": f"Update {filename}",
                "content": base64.b64encode(content).decode('utf-8'),
                "sha": data['sha'], "branch": GH_BRANCH
            }
            p = requests.put(url, headers=HEADERS, json=push)
            return (p.status_code in [200, 201]), "Saved"
            
        conn.close()
        return res, "OK"
    except Exception as e: return None, str(e)
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

@app.route('/update/<c>/<f>/<id>/<st>')
def update(c, f, id, st):
    def act(conn):
        conn.execute("UPDATE domains SET status=?, updated_at=? WHERE id=?", (st, int(time.time()), id))
        conn.commit()
        return "SAVE"
    fetch_and_edit_db(c, f, act)
    return redirect(url_for('manage_db', country=c, filename=f))

@app.route('/bulk_action/<c>/<f>', methods=['POST'])
def bulk(c, f):
    t, a = request.form.get('target'), request.form.get('action')
    def act(conn):
        if a == 'delete': conn.execute("DELETE FROM domains WHERE status=?", (t,))
        else: conn.execute("UPDATE domains SET status=? WHERE status=?", (a, t))
        conn.commit()
        return "SAVE"
    fetch_and_edit_db(c, f, act)
    return redirect(url_for('manage_db', country=c, filename=f))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
