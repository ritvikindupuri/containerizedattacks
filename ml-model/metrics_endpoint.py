"""
Prometheus metrics endpoint for ML service
"""

from flask import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def setup_metrics_endpoint(app):
    """Add /metrics endpoint to Flask app"""
    
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
