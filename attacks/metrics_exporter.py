#!/usr/bin/env python3
"""
Prometheus metrics exporter for attacks
Exposes attack metrics on port 9090
"""

from flask import Flask, Response, request, jsonify
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# Prometheus metrics
attack_total = Counter('attack_total', 'Total attacks executed', ['attack_type', 'status'])
attack_duration = Gauge('attack_duration_seconds', 'Attack duration', ['attack_type'])
attack_last_seen = Gauge('attack_last_seen_seconds', 'Unix timestamp of last attack execution', ['attack_type'])
containers_affected = Gauge('containers_affected_total', 'Containers affected by attacks')
security_events = Counter('security_events_total', 'Security events generated', ['priority', 'container'])

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/health')
def health():
    """Health check"""
    return {'status': 'healthy'}

@app.route('/record_attack', methods=['POST'])
def record_attack():
    """Record attack execution"""
    try:
        data = request.get_json()
        attack_type = data.get('attack_type')
        status = data.get('status', 'success')
        duration = data.get('duration', 0)
        affected = data.get('affected_containers', [])
        
        # Record metrics
        attack_total.labels(attack_type=attack_type, status=status).inc()
        attack_duration.labels(attack_type=attack_type).set(duration)
        attack_last_seen.labels(attack_type=attack_type).set(time.time())
        
        # Record security events
        priority = 'CRITICAL' if status == 'success' else 'LOW'
        for container in affected:
            security_events.labels(priority=priority, container=container).inc()
        
        # Update affected containers count
        if status == 'success':
            current = containers_affected._value.get()
            containers_affected.set(current + len(affected))
        
        return jsonify({'status': 'recorded'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Attack Metrics Exporter starting on port 9090")
    print("Waiting for attacks to execute...")
    app.run(host='0.0.0.0', port=9090, debug=False)
