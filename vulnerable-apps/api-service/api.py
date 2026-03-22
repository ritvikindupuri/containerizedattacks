#!/usr/bin/env python3
"""
E-Commerce API Service - Production-like vulnerable application
Simulates a real company's backend API with customer data, orders, payments
"""

from flask import Flask, request, jsonify, session
import psycopg2
import os
import subprocess
import jwt
import hashlib
import json
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
# DEMO ONLY — fake secret key for vulnerability demonstration
app.secret_key = 'prod_secret_key_2024_do_not_share'

# DEMO ONLY — fake database credentials to simulate credential exposure vulnerability
DB_CONFIG = {
    'host': 'vulnerable-db',
    'database': 'appdb',
    'user': 'admin',
    'password': 'Pr0d_P@ssw0rd_2024!'
}

# DEMO ONLY — simulated payment gateway credentials (intentionally hardcoded to demonstrate credential exposure)
PAYMENT_CONFIG = {
    'stripe_secret': 'DEMO_STRIPE_SECRET_KEY_NOT_REAL',
    'stripe_public': 'DEMO_STRIPE_PUBLIC_KEY_NOT_REAL',
    'paypal_client_id': 'DEMO_PAYPAL_CLIENT_ID_NOT_REAL',
    'paypal_secret': 'DEMO_PAYPAL_SECRET_NOT_REAL'
}

# DEMO ONLY — AWS example keys from AWS documentation (not real credentials)
AWS_CONFIG = {
    'access_key': 'AKIAIOSFODNN7EXAMPLE',
    'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    'region': 'us-east-1',
    's3_bucket': 'company-customer-data-prod'
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def generate_token(user_id, role='customer'):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'ecommerce-api',
        'version': '2.4.1',
        'environment': 'production',
        'container_id': os.getenv('HOSTNAME'),
        'uptime': '45d 12h 34m'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Customer login endpoint - SQL injection vulnerable"""
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        # Vulnerable: SQL injection
        query = f"SELECT id, email, role, first_name, last_name FROM users WHERE email='{email}' AND password='{password}'"
        cur.execute(query)
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            token = generate_token(user[0], user[2])
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'role': user[2],
                    'name': f"{user[3]} {user[4]}"
                }
            })
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get customer list - No authentication check"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, email, first_name, last_name, phone, address, 
                   credit_card_last4, total_orders, total_spent 
            FROM users WHERE role='customer' LIMIT 100
        """)
        customers = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'customers': [{
                'id': c[0], 'email': c[1], 'first_name': c[2], 
                'last_name': c[3], 'phone': c[4], 'address': c[5],
                'credit_card_last4': c[6], 'total_orders': c[7], 
                'total_spent': float(c[8]) if c[8] else 0
            } for c in customers]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get orders - SQL injection via query params"""
    user_id = request.args.get('user_id', '')
    status = request.args.get('status', '')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        # Vulnerable: SQL injection through query params
        query = f"SELECT * FROM orders WHERE user_id={user_id if user_id else '1=1'}"
        if status:
            query += f" AND status='{status}'"
        cur.execute(query)
        orders = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'orders': [dict(zip(['id', 'user_id', 'total', 'status', 'created_at'], o)) for o in orders]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment/process', methods=['POST'])
def process_payment():
    """Process payment - Exposes payment credentials"""
    data = request.get_json()
    
    return jsonify({
        'success': True,
        'transaction_id': secrets.token_hex(16),
        'payment_gateway': 'stripe',
        'credentials_used': {
            'stripe_key': 'DEMO_STRIPE_SECRET_KEY_NOT_REAL',
            'environment': 'production'
        },
        'amount': data.get('amount'),
        'currency': 'USD'
    })

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    """Admin endpoint - No authorization check"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, email, role, first_name, last_name, created_at FROM users")
        users = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'users': [{
                'id': u[0], 'email': u[1], 'role': u[2],
                'name': f"{u[3]} {u[4]}", 'created_at': str(u[5])
            } for u in users]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/exec', methods=['POST'])
def admin_exec():
    """Admin command execution - Command injection"""
    data = request.get_json()
    cmd = data.get('command', '')
    
    try:
        # Vulnerable: Command injection
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return jsonify({'output': result.decode()})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timeout'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config')
def get_config():
    """Expose configuration - Information disclosure"""
    return jsonify({
        'database': DB_CONFIG,
        'payment_gateways': PAYMENT_CONFIG,
        'aws': AWS_CONFIG,
        'redis': {
            'host': 'redis-cache.internal',
            'password': 'R3d1s_C@che_P@ss'
        },
        'smtp': {
            'host': 'smtp.company.com',
            'user': 'noreply@company.com',
            'password': 'Smtp_P@ss_2024'
        },
        'api_keys': {
            'sendgrid': 'SG.xYz123AbC456DeF789',
            'twilio': 'AC1234567890abcdef',
            'google_maps': 'AIzaSyD1234567890abcdef'
        }
    })

@app.route('/api/logs')
def get_logs():
    """Access logs - Path traversal"""
    log_file = request.args.get('file', '/var/log/app.log')
    try:
        # Vulnerable: Path traversal
        with open(log_file, 'r') as f:
            return jsonify({'logs': f.read()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup', methods=['POST'])
def create_backup():
    """Database backup - Command injection"""
    data = request.get_json()
    backup_name = data.get('name', 'backup')
    
    try:
        # Vulnerable: Command injection through backup name
        cmd = f"pg_dump -h {DB_CONFIG['host']} -U {DB_CONFIG['user']} {DB_CONFIG['database']} > /tmp/{backup_name}.sql"
        subprocess.run(cmd, shell=True, check=True)
        return jsonify({'success': True, 'backup_file': f'/tmp/{backup_name}.sql'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return f"""# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{{method="GET",endpoint="/api/customers"}} 15234
api_requests_total{{method="POST",endpoint="/api/orders"}} 8921
api_requests_total{{method="POST",endpoint="/api/payment/process"}} 4532

# HELP api_response_time_seconds API response time
# TYPE api_response_time_seconds histogram
api_response_time_seconds_bucket{{le="0.1"}} 12453
api_response_time_seconds_bucket{{le="0.5"}} 18234
api_response_time_seconds_bucket{{le="1.0"}} 19821

# HELP database_connections Active database connections
# TYPE database_connections gauge
database_connections 45

# HELP payment_transactions_total Total payment transactions
# TYPE payment_transactions_total counter
payment_transactions_total{{status="success"}} 4321
payment_transactions_total{{status="failed"}} 211
"""

if __name__ == '__main__':
    print("=" * 70)
    print("E-Commerce API Service - Production Environment")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['database']}")
    print(f"Payment Gateway: Stripe (Live Mode)")
    print(f"AWS S3 Bucket: {AWS_CONFIG['s3_bucket']}")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=False)
