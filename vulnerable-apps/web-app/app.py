#!/usr/bin/env python3
"""
Customer Portal Web Application - Production-like vulnerable app
Simulates a real company's customer-facing portal with authentication, profiles, orders
"""

from flask import Flask, request, render_template_string, session, redirect, url_for
import os
import subprocess
import psycopg2
import hashlib
from datetime import datetime

app = Flask(__name__)
# DEMO ONLY — fake secret key for vulnerability demonstration
app.secret_key = 'customer_portal_secret_2024'

# DEMO ONLY — fake database credentials to simulate credential exposure vulnerability
DB_CONFIG = {
    'host': 'vulnerable-db',
    'database': 'appdb',
    'user': 'admin',
    'password': 'Pr0d_P@ssw0rd_2024!'
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# Production-like HTML templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Customer Portal - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 400px;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover { background: #5568d3; }
        .error { color: #e74c3c; margin-bottom: 15px; padding: 10px; background: #fadbd8; border-radius: 5px; }
        .demo-creds {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            font-size: 12px;
        }
        .demo-creds strong { color: #667eea; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>Customer Portal</h1>
        <p class="subtitle">Access your account and manage orders</p>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label>Email Address</label>
                <input type="text" name="email" placeholder="your.email@example.com" required />
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" placeholder="Enter your password" required />
            </div>
            <button type="submit">Sign In</button>
        </form>
        
        <div class="demo-creds">
            <strong>Demo Accounts:</strong><br>
            Customer: john.doe@email.com / password123<br>
            Admin: admin@company.com / admin2024
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Customer Portal - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
        }
        .header {
            background: white;
            padding: 20px 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { color: #667eea; font-size: 24px; }
        .user-info { color: #666; }
        .logout { color: #e74c3c; text-decoration: none; margin-left: 20px; }
        .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-card .value { font-size: 32px; font-weight: bold; color: #667eea; }
        .section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section h2 { color: #333; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; color: #666; font-weight: 600; }
        .status { padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .status.completed { background: #d4edda; color: #155724; }
        .status.pending { background: #fff3cd; color: #856404; }
        .status.shipped { background: #d1ecf1; color: #0c5460; }
        .search-form { margin-bottom: 20px; }
        .search-form input { padding: 10px; width: 300px; border: 1px solid #ddd; border-radius: 5px; }
        .search-form button { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Customer Portal</h1>
        <div>
            <span class="user-info">Welcome, {{ user_name }}</span>
            <a href="/logout" class="logout">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>Total Orders</h3>
                <div class="value">{{ stats.total_orders }}</div>
            </div>
            <div class="stat-card">
                <h3>Total Spent</h3>
                <div class="value">${{ "%.2f"|format(stats.total_spent) }}</div>
            </div>
            <div class="stat-card">
                <h3>Pending Orders</h3>
                <div class="value">{{ stats.pending_orders }}</div>
            </div>
            <div class="stat-card">
                <h3>Account Status</h3>
                <div class="value" style="font-size: 20px; color: #28a745;">Active</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Recent Orders</h2>
            <table>
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>Date</th>
                        <th>Items</th>
                        <th>Total</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for order in orders %}
                    <tr>
                        <td>#{{ order.id }}</td>
                        <td>{{ order.created_at }}</td>
                        <td>{{ order.items }}</td>
                        <td>${{ "%.2f"|format(order.total) }}</td>
                        <td><span class="status {{ order.status }}">{{ order.status }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Search Orders (Admin)</h2>
            <form method="POST" action="/search" class="search-form">
                <input type="text" name="query" placeholder="Search by order ID, customer email, or SQL query..." />
                <button type="submit">Search</button>
            </form>
            {% if search_results %}
            <h3>Search Results:</h3>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">{{ search_results }}</pre>
            {% endif %}
        </div>
        
        <div class="section">
            <h2>System Commands (Admin Only)</h2>
            <form method="POST" action="/admin/command" class="search-form">
                <input type="text" name="cmd" placeholder="Enter system command..." />
                <button type="submit">Execute</button>
            </form>
            {% if cmd_output %}
            <h3>Command Output:</h3>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">{{ cmd_output }}</pre>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        # Vulnerable: SQL injection
        query = f"SELECT id, email, first_name, last_name, role FROM users WHERE email='{email}' AND password='{password}'"
        cur.execute(query)
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = f"{user[2]} {user[3]}"
            session['role'] = user[4]
            return redirect('/dashboard')
        
        return render_template_string(LOGIN_TEMPLATE, error="Invalid email or password")
    except Exception as e:
        return render_template_string(LOGIN_TEMPLATE, error=f"Error: {str(e)}")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get user stats
        cur.execute(f"SELECT total_orders, total_spent FROM users WHERE id={session['user_id']}")
        stats_data = cur.fetchone()
        
        # Get pending orders count
        cur.execute(f"SELECT COUNT(*) FROM orders WHERE user_id={session['user_id']} AND status='pending'")
        pending = cur.fetchone()[0]
        
        # Get recent orders
        cur.execute(f"""
            SELECT id, created_at, total, status, 
                   (SELECT COUNT(*) FROM order_items WHERE order_id=orders.id) as items
            FROM orders WHERE user_id={session['user_id']} 
            ORDER BY created_at DESC LIMIT 10
        """)
        orders = cur.fetchall()
        
        cur.close()
        conn.close()
        
        stats = {
            'total_orders': stats_data[0] if stats_data else 0,
            'total_spent': float(stats_data[1]) if stats_data and stats_data[1] else 0.0,
            'pending_orders': pending
        }
        
        orders_list = [{
            'id': o[0],
            'created_at': o[1].strftime('%Y-%m-%d %H:%M') if o[1] else 'N/A',
            'total': float(o[2]) if o[2] else 0.0,
            'status': o[3],
            'items': o[4]
        } for o in orders]
        
        return render_template_string(DASHBOARD_TEMPLATE, 
                                     user_name=session['user_name'],
                                     stats=stats,
                                     orders=orders_list)
    except Exception as e:
        return f"Error loading dashboard: {str(e)}"

@app.route('/search', methods=['POST'])
def search():
    """Vulnerable search - SQL injection"""
    if 'user_id' not in session:
        return redirect('/')
    
    query = request.form.get('query', '')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        # Vulnerable: Direct SQL injection
        search_query = f"SELECT * FROM orders WHERE id::text LIKE '%{query}%' OR status LIKE '%{query}%'"
        cur.execute(search_query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template_string(DASHBOARD_TEMPLATE,
                                     user_name=session['user_name'],
                                     stats={'total_orders': 0, 'total_spent': 0, 'pending_orders': 0},
                                     orders=[],
                                     search_results=str(results))
    except Exception as e:
        return render_template_string(DASHBOARD_TEMPLATE,
                                     user_name=session['user_name'],
                                     stats={'total_orders': 0, 'total_spent': 0, 'pending_orders': 0},
                                     orders=[],
                                     search_results=f"Error: {str(e)}")

@app.route('/admin/command', methods=['POST'])
def admin_command():
    """Vulnerable command execution"""
    if 'user_id' not in session:
        return redirect('/')
    
    cmd = request.form.get('cmd', '')
    
    try:
        # Vulnerable: Command injection
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return render_template_string(DASHBOARD_TEMPLATE,
                                     user_name=session['user_name'],
                                     stats={'total_orders': 0, 'total_spent': 0, 'pending_orders': 0},
                                     orders=[],
                                     cmd_output=output.decode())
    except Exception as e:
        return render_template_string(DASHBOARD_TEMPLATE,
                                     user_name=session['user_name'],
                                     stats={'total_orders': 0, 'total_spent': 0, 'pending_orders': 0},
                                     orders=[],
                                     cmd_output=f"Error: {str(e)}")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/health')
def health():
    return {'status': 'running', 'service': 'customer-portal', 'container': os.getenv('HOSTNAME')}

if __name__ == '__main__':
    print("=" * 70)
    print("Customer Portal Web Application - Production Environment")
    print("=" * 70)
    print("Demo Accounts:")
    print("  Customer: john.doe@email.com / password123")
    print("  Admin: admin@company.com / admin2024")
    print("=" * 70)
    app.run(host='0.0.0.0', port=80, debug=False)
