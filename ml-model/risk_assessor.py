#!/usr/bin/env python3
"""
Risk Assessor - ML-based risk scoring for container security events
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import json

class RiskAssessor:
    """
    Machine Learning risk assessor for container security events
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_count = 0
        
        # Risk thresholds
        self.CRITICAL_THRESHOLD = 0.8
        self.HIGH_THRESHOLD = 0.6
        self.MEDIUM_THRESHOLD = 0.4
        self.LOW_THRESHOLD = 0.2
    
    def assess_risk(self, features):
        """
        Assess risk score for given features
        Returns: float between 0 and 1
        """
        if self.model is None:
            # Fallback to rule-based scoring if no model
            return self._rule_based_score(features)
        
        try:
            # Prepare features
            feature_vector = self._prepare_features(features)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform([feature_vector])
            
            # Predict probability
            risk_proba = self.model.predict_proba(feature_vector_scaled)[0]
            
            # Return probability of high-risk class
            return risk_proba[1] if len(risk_proba) > 1 else risk_proba[0]
        
        except Exception as e:
            print(f"Error in risk assessment: {e}")
            return self._rule_based_score(features)
    
    def _rule_based_score(self, features):
        """
        Fallback rule-based risk scoring
        """
        score = 0.0
        
        # Priority-based scoring
        priority_scores = {
            'CRITICAL': 0.9,
            'HIGH': 0.7,
            'MEDIUM': 0.5,
            'LOW': 0.3,
            'NOTICE': 0.1
        }
        score += priority_scores.get(features.get('priority', 'MEDIUM'), 0.5)
        
        # Rule-based scoring
        rule = features.get('rule', '').lower()
        if 'escape' in rule or 'privileged' in rule:
            score += 0.3
        elif 'namespace' in rule or 'cgroup' in rule:
            score += 0.25
        elif 'capability' in rule or 'privilege' in rule:
            score += 0.2
        elif 'network' in rule or 'scanning' in rule:
            score += 0.15
        
        # Container-specific factors
        if features.get('is_privileged', False):
            score += 0.2
        
        if features.get('has_docker_socket', False):
            score += 0.25
        
        # Normalize to 0-1
        return min(score, 1.0)
    
    def get_risk_level(self, risk_score):
        """
        Convert risk score to risk level
        """
        if risk_score >= self.CRITICAL_THRESHOLD:
            return 'CRITICAL'
        elif risk_score >= self.HIGH_THRESHOLD:
            return 'HIGH'
        elif risk_score >= self.MEDIUM_THRESHOLD:
            return 'MEDIUM'
        elif risk_score >= self.LOW_THRESHOLD:
            return 'LOW'
        else:
            return 'INFO'
    
    def _prepare_features(self, features):
        """
        Convert feature dict to vector
        """
        # Feature vector (must match training)
        vector = [
            1.0 if features.get('priority') == 'CRITICAL' else 0.0,
            1.0 if features.get('priority') == 'HIGH' else 0.0,
            1.0 if features.get('priority') == 'MEDIUM' else 0.0,
            1.0 if features.get('is_privileged', False) else 0.0,
            1.0 if features.get('has_docker_socket', False) else 0.0,
            1.0 if features.get('has_host_mount', False) else 0.0,
            float(features.get('process_count', 0)),
            float(features.get('file_access_count', 0)),
            float(features.get('network_connections', 0)),
            1.0 if 'escape' in features.get('rule', '').lower() else 0.0,
            1.0 if 'namespace' in features.get('rule', '').lower() else 0.0,
            1.0 if 'capability' in features.get('rule', '').lower() else 0.0,
        ]
        
        return np.array(vector)
    
    def train_from_file(self, events_file):
        """
        Train model from events file
        """
        print(f"Training model from {events_file}")
        
        # Load events
        events = []
        with open(events_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except:
                    continue
        
        if len(events) < 10:
            print(f"Not enough events for training: {len(events)}")
            return {'error': 'Insufficient training data'}
        
        print(f"Loaded {len(events)} events")
        
        # Extract features and labels
        from event_processor import EventProcessor
        processor = EventProcessor()
        
        X = []
        y = []
        
        for event in events:
            features = processor.extract_features(event)
            feature_vector = self._prepare_features(features)
            X.append(feature_vector)
            
            # Label based on priority
            priority = event.get('priority', 'MEDIUM')
            label = 1 if priority in ['CRITICAL', 'HIGH'] else 0
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"Training data shape: {X.shape}")
        print(f"High-risk events: {sum(y)}/{len(y)}")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_scaled, y)
        self.feature_count = X.shape[1]
        
        # Calculate metrics
        train_score = self.model.score(X_scaled, y)
        
        print(f"Model trained successfully")
        print(f"Training accuracy: {train_score:.3f}")
        
        return {
            'training_samples': len(X),
            'high_risk_samples': int(sum(y)),
            'accuracy': float(train_score),
            'features': int(self.feature_count)
        }
    
    def save_model(self, path):
        """Save model to disk"""
        if self.model is None:
            print("No model to save")
            return
        
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_count': self.feature_count
        }, path)
        
        print(f"Model saved to {path}")
    
    def load_model(self, path):
        """Load model from disk"""
        try:
            data = joblib.load(path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.feature_count = data['feature_count']
            print(f"Model loaded from {path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
