#!/usr/bin/env python3
"""
Event Processor - Extract features from security events
"""

import json
from collections import defaultdict
from datetime import datetime

class EventProcessor:
    """
    Process security events and extract features for ML
    """
    
    def __init__(self):
        self.event_counts = defaultdict(int)
        self.rule_counts = defaultdict(int)
        self.container_counts = defaultdict(int)
    
    def extract_features(self, event):
        """
        Extract features from a security event
        """
        features = {}
        
        # Basic event info
        features['priority'] = event.get('priority', 'MEDIUM')
        features['rule'] = event.get('rule', 'Unknown')
        features['time'] = event.get('time', '')
        
        # Output fields
        output_fields = event.get('output_fields', {})
        
        # Container info
        features['container_name'] = output_fields.get('container.name', 'unknown')
        features['container_id'] = output_fields.get('container.id', 'unknown')
        features['container_image'] = output_fields.get('container.image', 'unknown')
        
        # Check for privileged container
        features['is_privileged'] = (
            'privileged' in features['rule'].lower() or
            output_fields.get('container.privileged', 'false') == 'true'
        )
        
        # Check for Docker socket access
        features['has_docker_socket'] = (
            'docker.sock' in str(output_fields.get('fd.name', '')) or
            'docker' in features['rule'].lower()
        )
        
        # Check for host filesystem mount
        features['has_host_mount'] = (
            '/host' in str(output_fields.get('fd.name', '')) or
            'host' in features['rule'].lower()
        )
        
        # Process info
        features['process_name'] = output_fields.get('proc.name', 'unknown')
        features['process_cmdline'] = output_fields.get('proc.cmdline', '')
        features['user_name'] = output_fields.get('user.name', 'unknown')
        
        # File access
        features['file_name'] = output_fields.get('fd.name', '')
        features['file_access_count'] = 1  # Simplified
        
        # Network info
        features['network_connections'] = 1 if 'network' in features['rule'].lower() else 0
        
        # Process count (simplified)
        features['process_count'] = 1
        
        # Update statistics
        self.event_counts[features['priority']] += 1
        self.rule_counts[features['rule']] += 1
        self.container_counts[features['container_name']] += 1
        
        return features
    
    def get_statistics(self):
        """
        Get statistics about processed events
        """
        return {
            'total_events': sum(self.event_counts.values()),
            'by_priority': dict(self.event_counts),
            'by_rule': dict(self.rule_counts),
            'by_container': dict(self.container_counts),
            'unique_rules': len(self.rule_counts),
            'unique_containers': len(self.container_counts)
        }
    
    def reset_statistics(self):
        """Reset statistics counters"""
        self.event_counts.clear()
        self.rule_counts.clear()
        self.container_counts.clear()
