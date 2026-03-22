#!/usr/bin/env python3
"""
ML Risk Assessment Service
Real-time risk scoring for container security events
"""

from flask import Flask, jsonify, request
import json
import os
from datetime import datetime
from risk_assessor import RiskAssessor
from event_processor import EventProcessor
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metrics
risk_score_gauge = Gauge('ml_risk_score', 'ML Risk Score', ['container', 'priority'])
events_processed = Counter('ml_events_processed_total', 'Total events processed')
risk_assessment_duration = Histogram('ml_risk_assessment_duration_seconds', 'Risk assessment duration')

# Initialize components
risk_assessor = RiskAssessor()
event_processor = EventProcessor()

# Load or train model on startup
MODEL_PATH = '/app/model.pkl'
if os.path.exists(MODEL_PATH):
    risk_assessor.load_model(MODEL_PATH)
    print("✓ Loaded existing ML model")
else:
    print("! No model found, will train on first events")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ml-risk-assessor',
        'model_loaded': risk_assessor.model is not None,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/assess', methods=['POST'])
def assess_event():
    """
    Assess risk for a single security event
    """
    try:
        with risk_assessment_duration.time():
            event = request.json
            
            # Extract features
            features = event_processor.extract_features(event)
            
            # Assess risk
            risk_score = risk_assessor.assess_risk(features)
            risk_level = risk_assessor.get_risk_level(risk_score)
            
            # Update Prometheus metrics
            container = features.get('container_name', 'unknown')
            priority = features.get('priority', 'UNKNOWN')
            risk_score_gauge.labels(container=container, priority=priority).set(risk_score * 100)
            events_processed.inc()
        
        return jsonify({
            'risk_score': float(risk_score),
            'risk_level': risk_level,
            'event_priority': event.get('priority', 'UNKNOWN'),
            'rule': event.get('rule', 'Unknown'),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/assess/batch', methods=['POST'])
def assess_batch():
    """
    Assess risk for multiple events
    """
    try:
        events = request.json.get('events', [])
        
        results = []
        for event in events:
            features = event_processor.extract_features(event)
            risk_score = risk_assessor.assess_risk(features)
            risk_level = risk_assessor.get_risk_level(risk_score)
            
            results.append({
                'rule': event.get('rule', 'Unknown'),
                'risk_score': float(risk_score),
                'risk_level': risk_level,
                'priority': event.get('priority', 'UNKNOWN')
            })
        
        return jsonify({
            'total_events': len(results),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/train', methods=['POST'])
def train_model():
    """
    Train the ML model on collected events
    """
    try:
        # Load events from logs
        events_file = '/logs/events.json'
        
        if not os.path.exists(events_file):
            return jsonify({'error': 'No events file found'}), 404
        
        # Train model
        metrics = risk_assessor.train_from_file(events_file)
        
        # Save model
        risk_assessor.save_model(MODEL_PATH)
        
        return jsonify({
            'status': 'success',
            'message': 'Model trained successfully',
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about processed events
    """
    try:
        stats = event_processor.get_statistics()
        
        return jsonify({
            'statistics': stats,
            'model_info': {
                'loaded': risk_assessor.model is not None,
                'type': 'Random Forest Classifier',
                'features': risk_assessor.feature_count if risk_assessor.model else 0
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/events/recent', methods=['GET'])
def get_recent_events():
    """
    Get recent events with risk scores
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        
        events_file = '/logs/events.json'
        if not os.path.exists(events_file):
            return jsonify({'events': []})
        
        # Read recent events
        events = []
        with open(events_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    features = event_processor.extract_features(event)
                    risk_score = risk_assessor.assess_risk(features)
                    
                    events.append({
                        'time': event.get('time', ''),
                        'rule': event.get('rule', 'Unknown'),
                        'priority': event.get('priority', 'UNKNOWN'),
                        'container': event.get('output_fields', {}).get('container.name', 'unknown'),
                        'risk_score': float(risk_score),
                        'risk_level': risk_assessor.get_risk_level(risk_score)
                    })
                    
                    if len(events) >= limit:
                        break
                except:
                    continue
        
        return jsonify({
            'events': events[-limit:],
            'total': len(events),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    from flask import Response
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    print("=" * 60)
    print("ML Risk Assessment Service Starting")
    print("=" * 60)
    print(f"Model path: {MODEL_PATH}")
    print(f"Logs path: /logs/events.json")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
