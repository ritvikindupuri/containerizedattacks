#!/usr/bin/env python3
"""
Standalone Dashboard Server - Run directly from your machine!
Connects to Docker Desktop to get real container metrics and attack data.

Usage: python run_dashboard.py
Then open: http://localhost:8888
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import os
import docker
import time
import threading
from datetime import datetime

app = Flask(__name__, template_folder='dashboard/templates', static_folder='dashboard/static')
CORS(app)

# Initialize Docker client (connects to Docker Desktop)
try:
    docker_client = docker.from_env()
    DOCKER_AVAILABLE = True
    print("✓ Connected to Docker Desktop")
except Exception as e:
    DOCKER_AVAILABLE = False
    print(f"✗ Docker not available: {e}")
    print("  Running in demo mode")

# Metrics cache — refresh at most once every 10s to avoid blocking on Docker stats
_metrics_cache = {}
_metrics_cache_time = {}
METRICS_CACHE_TTL = 10  # seconds

def get_container_metrics(container_name):
    """Get real-time metrics from Docker container, cached per TTL to avoid blocking."""
    if not DOCKER_AVAILABLE:
        return None

    now = time.time()
    if container_name in _metrics_cache and (now - _metrics_cache_time.get(container_name, 0)) < METRICS_CACHE_TTL:
        return _metrics_cache[container_name]

    try:
        container = docker_client.containers.get(container_name)
        stats = container.stats(stream=False)
        
        # Calculate CPU percentage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        
        percpu = stats['cpu_stats']['cpu_usage'].get('percpu_usage', [])
        num_cpus = len(percpu) if percpu else 1
        
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
        else:
            cpu_percent = 0.0
        
        # Calculate memory usage
        memory_usage = stats['memory_stats'].get('usage', 0)
        memory_limit = stats['memory_stats'].get('limit', 1)
        memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0
        
        # Network I/O
        network_rx = 0
        network_tx = 0
        if 'networks' in stats:
            for interface in stats['networks'].values():
                network_rx += interface.get('rx_bytes', 0)
                network_tx += interface.get('tx_bytes', 0)
        
        # Block I/O
        blkio_read = 0
        blkio_write = 0
        if 'blkio_stats' in stats and 'io_service_bytes_recursive' in stats['blkio_stats']:
            for entry in stats['blkio_stats']['io_service_bytes_recursive']:
                if entry['op'] == 'Read':
                    blkio_read += entry['value']
                elif entry['op'] == 'Write':
                    blkio_write += entry['value']
        
        result = {
            'cpu_percent': round(cpu_percent, 2),
            'memory_usage_mb': round(memory_usage / 1024 / 1024, 2),
            'memory_percent': round(memory_percent, 2),
            'network_rx_mb': round(network_rx / 1024 / 1024, 2),
            'network_tx_mb': round(network_tx / 1024 / 1024, 2),
            'disk_read_mb': round(blkio_read / 1024 / 1024, 2),
            'disk_write_mb': round(blkio_write / 1024 / 1024, 2)
        }
        _metrics_cache[container_name] = result
        _metrics_cache_time[container_name] = now
        return result
    except Exception as e:
        print(f"Error getting metrics for {container_name}: {e}")
        return None

def get_attack_metrics_from_container():
    """Get real attack metrics from the attack-orchestrator container"""
    if not DOCKER_AVAILABLE:
        return None

    try:
        container = docker_client.containers.get('attack-orchestrator')
        result = container.exec_run('curl -s http://localhost:9090/metrics')

        if result.exit_code == 0:
            metrics_text = result.output.decode('utf-8')
            attack_data = {}

            for line in metrics_text.split('\n'):
                line = line.strip()
                if line.startswith('attack_total{'):
                    try:
                        labels = line.split('{')[1].split('}')[0]
                        value = float(line.split('}')[1].strip())
                        attack_type = labels.split('attack_type="')[1].split('"')[0]
                        status = labels.split('status="')[1].split('"')[0]
                        if attack_type not in attack_data:
                            attack_data[attack_type] = {}
                        attack_data[attack_type]['status'] = status
                        attack_data[attack_type]['count'] = int(value)
                    except Exception:
                        pass

                elif line.startswith('attack_last_seen_seconds{'):
                    try:
                        labels = line.split('{')[1].split('}')[0]
                        timestamp_unix = float(line.split('}')[1].strip())
                        attack_type = labels.split('attack_type="')[1].split('"')[0]
                        timestamp_dt = datetime.utcfromtimestamp(timestamp_unix)
                        if attack_type not in attack_data:
                            attack_data[attack_type] = {}
                        attack_data[attack_type]['timestamp'] = timestamp_dt.isoformat() + 'Z'
                    except Exception:
                        pass

                elif line.startswith('attack_created{'):
                    try:
                        labels = line.split('{')[1].split('}')[0]
                        timestamp_unix = float(line.split('}')[1].strip())
                        attack_type = labels.split('attack_type="')[1].split('"')[0]
                        timestamp_dt = datetime.utcfromtimestamp(timestamp_unix)
                        if attack_type not in attack_data:
                            attack_data[attack_type] = {}
                        attack_data[attack_type]['timestamp'] = timestamp_dt.isoformat() + 'Z'
                    except Exception:
                        pass

            # Build result — include entry even if timestamp is missing
            attacks = []
            for attack_type, data in attack_data.items():
                if 'count' in data:
                    attacks.append({
                        'attack_type': attack_type,
                        'status': data.get('status', 'unknown'),
                        'count': data['count'],
                        'timestamp': data.get('timestamp', datetime.utcnow().isoformat() + 'Z')
                    })

            print(f"✓ Parsed {len(attacks)} attacks from metrics endpoint")
            return attacks if attacks else None

    except Exception as e:
        print(f"Could not get metrics from container: {e}")

    return None

@app.route('/')
def index():
    """Render dashboard with real Docker metrics and attack data"""
    
    # Get real attack metrics from container
    raw_attacks = get_attack_metrics_from_container()
    
    # MITRE ATT&CK mappings
    MITRE_MAPPINGS = {
        'docker_socket_escape': {
            'tactics': 'Privilege Escalation, Defense Evasion',
            'techniques': 'T1611 - Escape to Host',
            'severity': 'Docker socket = root on host. Bypasses ALL container isolation.'
        },
        'namespace_manipulation': {
            'tactics': 'Privilege Escalation, Defense Evasion',
            'techniques': 'T1611 - Escape to Host, T1055 - Process Injection',
            'severity': 'Breaks Linux namespace isolation. Provides host filesystem access via /proc/1/root.'
        },
        'resource_abuse': {
            'tactics': 'Impact',
            'techniques': 'T1496 - Resource Hijacking, T1499 - Endpoint DoS',
            'severity': 'Disruptive but no privilege escalation. Resource limits enforced.'
        },
        'network_attacks': {
            'tactics': 'Discovery, Lateral Movement',
            'techniques': 'T1046 - Network Service Discovery, T1021 - Remote Services',
            'severity': 'Enables lateral movement in microservices. Container networks often lack segmentation.'
        },
        'capability_abuse': {
            'tactics': 'Privilege Escalation, Defense Evasion',
            'techniques': 'T1611 - Escape to Host, T1068 - Privilege Escalation',
            'severity': 'CAP_SYS_ADMIN ≈ root access. Can mount host filesystems and bypass security controls.'
        },
        'image_registry': {
            'tactics': 'Initial Access, Persistence',
            'techniques': 'T1525 - Implant Internal Image, T1552.001 - Credentials In Files',
            'severity': 'Supply chain attack. Compromised images affect entire organization across all deployments.'
        },
        'privileged_container_escape': {
            'tactics': 'Privilege Escalation',
            'techniques': 'T1611 - Escape to Host',
            'severity': '--privileged flag disables all security. Full device access and host compromise.'
        }
    }
    
    # Failure reasons
    FAILURE_REASONS = {
        'privileged_container_escape': 'Attack requires --privileged flag. Container is running in non-privileged mode (security control working as intended).',
        'docker_socket_escape': 'Docker socket not mounted in container. Security control preventing socket access.',
        'namespace_manipulation': 'Namespace isolation enforced. Cannot access host namespaces.',
        'capability_abuse': 'Dangerous capabilities not granted. Container running with minimal capabilities.',
        'resource_abuse': 'Resource limits enforced. cgroups preventing resource exhaustion.',
        'network_attacks': 'Network policies blocking lateral movement. Container network segmentation active.',
        'image_registry': 'Registry access denied. Authentication required for image operations.'
    }
    
    # Build attack data
    attacks = []
    
    if raw_attacks:
        # Use real data from container
        for attack in raw_attacks:
            attack_type = attack['attack_type']
            mitre = MITRE_MAPPINGS.get(attack_type, {'tactics': 'Unknown', 'techniques': 'Unknown', 'severity': 'Unknown'})

            # Feature breakdown — risk_score derived from sum so math always adds up
            FEATURE_SCORES = {
                'docker_socket_escape':        {'Privilege Escalation': (100, 0.25), 'Host Access': (100, 0.25), 'Data Exfiltration': (85, 0.20), 'Lateral Movement': (70, 0.15), 'Persistence': (90, 0.15)},
                'namespace_manipulation':      {'Privilege Escalation': (95, 0.25),  'Host Access': (98, 0.25),  'Data Exfiltration': (80, 0.20), 'Lateral Movement': (75, 0.15), 'Persistence': (60, 0.15)},
                'resource_abuse':              {'Privilege Escalation': (30, 0.25),  'Host Access': (25, 0.25),  'Data Exfiltration': (40, 0.20), 'Lateral Movement': (35, 0.15), 'Persistence': (30, 0.15)},
                'network_attacks':             {'Privilege Escalation': (50, 0.25),  'Host Access': (45, 0.25),  'Data Exfiltration': (90, 0.20), 'Lateral Movement': (95, 0.15), 'Persistence': (65, 0.15)},
                'capability_abuse':            {'Privilege Escalation': (95, 0.25),  'Host Access': (85, 0.25),  'Data Exfiltration': (75, 0.20), 'Lateral Movement': (60, 0.15), 'Persistence': (80, 0.15)},
                'image_registry':              {'Privilege Escalation': (80, 0.25),  'Host Access': (70, 0.25),  'Data Exfiltration': (95, 0.20), 'Lateral Movement': (75, 0.15), 'Persistence': (95, 0.15)},
                'privileged_container_escape': {'Privilege Escalation': (100, 0.25), 'Host Access': (100, 0.25), 'Data Exfiltration': (95, 0.20), 'Lateral Movement': (85, 0.15), 'Persistence': (95, 0.15)},
            }
            features = FEATURE_SCORES.get(attack_type, {})
            risk_score = round(sum(s * w for s, w in features.values()), 1)
            risk_level = 'CRITICAL' if risk_score >= 80 else 'HIGH' if risk_score >= 60 else 'MEDIUM' if risk_score >= 40 else 'LOW'
            ml_data = {
                'score': risk_score,
                'level': risk_level,
                'features': [
                    {
                        'name': feat,
                        'score': score,
                        'weight': weight,
                        'contribution': round(score * weight, 1)
                    }
                    for feat, (score, weight) in features.items()
                ]
            }

            attacks.append({
                'name': attack_type.replace('_', ' ').title(),
                'type': attack_type,
                'status': attack['status'],
                'risk_score': risk_score,
                'risk_level': risk_level,
                'ml_data': ml_data,
                'ml_calculation': '',
                'mitre_tactics': mitre['tactics'],
                'severity_reason': mitre['severity'],
                'failure_reason': FAILURE_REASONS.get(attack_type, 'Attack did not meet success criteria.') if attack['status'] == 'failed' else None
            })
    else:
        # No real data - show message instead of demo data
        attacks = []
    
    # Calculate stats
    total_attacks = len(attacks)
    successful = sum(1 for a in attacks if a['status'] == 'success')
    success_rate = round((successful / total_attacks * 100) if total_attacks > 0 else 0, 1)
    
    # Risk distribution
    risk_dist = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for attack in attacks:
        risk_dist[attack['risk_level']] += 1
    
    # Build donut chart slices
    import math
    pie_slices = []
    colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#a855f7', '#ec4899']
    mitre_ids = {
        'docker_socket_escape': 'T1611',
        'privileged_container_escape': 'T1611',
        'namespace_manipulation': 'T1611',
        'resource_abuse': 'T1496',
        'network_attacks': 'T1046',
        'capability_abuse': 'T1611',
        'image_registry': 'T1525'
    }

    if attacks:
        total = len(attacks)
        start_angle = 0
        cx, cy = 160, 160
        outer_r = 150
        # label sits in the middle of the ring band (outer=150, inner=75 => midpoint ~112)
        label_r = 112

        for idx, attack in enumerate(attacks):
            slice_percent = round((1.0 / total) * 100, 1)
            angle_size = 360.0 / total
            end_angle = start_angle + angle_size
            mid_angle = start_angle + angle_size / 2

            start_rad = math.radians(start_angle - 90)
            end_rad   = math.radians(end_angle - 90)
            mid_rad   = math.radians(mid_angle - 90)

            x1 = cx + outer_r * math.cos(start_rad)
            y1 = cy + outer_r * math.sin(start_rad)
            x2 = cx + outer_r * math.cos(end_rad)
            y2 = cy + outer_r * math.sin(end_rad)

            large_arc = 1 if angle_size > 180 else 0

            lx = cx + label_r * math.cos(mid_rad)
            ly = cy + label_r * math.sin(mid_rad)

            mitre_id = mitre_ids.get(attack['type'], 'T0000')

            pie_slices.append({
                'path': f"M {cx} {cy} L {x1:.1f} {y1:.1f} A {outer_r} {outer_r} 0 {large_arc} 1 {x2:.1f} {y2:.1f} Z",
                'color': colors[idx % len(colors)],
                'percentage': slice_percent,
                'name': attack['name'],
                'mitre_id': mitre_id,
                'label_x': round(lx, 1),
                'label_y': round(ly, 1),
            })

            start_angle = end_angle
    
    # Build infrastructure data with REAL Docker metrics
    infrastructure = []
    container_targets = {
        'docker_socket_escape': [
            {'container': 'attack-orchestrator', 'target': 'Docker Socket API', 'component': '/var/run/docker.sock'},
            {'container': 'vulnerable-web', 'target': 'Flask Application', 'component': 'Customer Portal Web Server'},
            {'container': 'privileged-container', 'target': 'Privileged Runtime', 'component': 'Host PID namespace'}
        ],
        'namespace_manipulation': [
            {'container': 'attack-orchestrator', 'target': 'Linux Namespaces', 'component': '/proc/1/root filesystem'},
            {'container': 'attack-orchestrator', 'target': 'PID Namespace', 'component': 'Host process tree'}
        ],
        'resource_abuse': [
            {'container': 'attack-orchestrator', 'target': 'CPU Scheduler', 'component': 'Process spawning'},
            {'container': 'attack-orchestrator', 'target': 'Memory Allocator', 'component': 'Heap memory'},
            {'container': 'attack-orchestrator', 'target': 'Disk I/O', 'component': '/tmp filesystem'}
        ],
        'network_attacks': [
            {'container': 'vulnerable-web', 'target': 'Flask Web Server', 'component': 'Port 80 HTTP service'},
            {'container': 'vulnerable-api', 'target': 'Payment API', 'component': 'Port 5000 REST API'},
            {'container': 'vulnerable-db', 'target': 'PostgreSQL Database', 'component': 'Port 5432 database service'}
        ],
        'capability_abuse': [
            {'container': 'attack-orchestrator', 'target': 'CAP_SYS_ADMIN', 'component': 'Mount syscall'},
            {'container': 'attack-orchestrator', 'target': 'CAP_NET_ADMIN', 'component': 'Network configuration'}
        ],
        'image_registry': [
            {'container': 'attack-orchestrator', 'target': 'Docker Registry', 'component': 'Image layers'},
            {'container': 'attack-orchestrator', 'target': 'Docker Config', 'component': '~/.docker/config.json'}
        ],
        'privileged_container_escape': [
            {'container': 'privileged-container', 'target': 'Privileged Runtime', 'component': 'Host device access'}
        ]
    }
    
    for attack in attacks:
        targets = container_targets.get(attack['type'], [])
        for target in targets:
            # Get REAL metrics from Docker
            metrics = get_container_metrics(target['container'])
            
            impact_descriptions = {
                'docker_socket_escape': 'Full host access via Docker daemon',
                'namespace_manipulation': 'Host filesystem access via proc',
                'resource_abuse': 'CPU/Memory/Disk exhaustion',
                'network_attacks': 'Service discovery and enumeration',
                'capability_abuse': 'Host filesystem mount capability',
                'image_registry': 'Secret extraction from images',
                'privileged_container_escape': 'Full device access via --privileged'
            }
            
            infrastructure.append({
                'attack_name': attack['name'],
                'container': target['container'],
                'target_component': target['target'],
                'specific_target': target['component'],
                'impact_description': impact_descriptions.get(attack['type'], 'Security impact'),
                'metrics': metrics
            })
    
    return render_template('index.html',
        attacks=attacks,
        infrastructure=infrastructure,
        pie_slices=pie_slices,
        total_attacks=total_attacks,
        success_rate=success_rate,
        risk_distribution=risk_dist,
        last_update=datetime.now().strftime('%H:%M:%S')
    )

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for real-time metrics"""
    return jsonify({'status': 'ok'})

@app.route('/api/dashboard')
def api_dashboard():
    """Full dashboard data as JSON — polled every 3s by the frontend"""
    raw_attacks = get_attack_metrics_from_container()

    MITRE_MAPPINGS = {
        'docker_socket_escape':        {'tactics': 'Privilege Escalation, Defense Evasion', 'severity': 'Docker socket = root on host. Bypasses ALL container isolation.'},
        'namespace_manipulation':      {'tactics': 'Privilege Escalation, Defense Evasion', 'severity': 'Breaks Linux namespace isolation. Provides host filesystem access via /proc/1/root.'},
        'resource_abuse':              {'tactics': 'Impact',                                 'severity': 'Disruptive but no privilege escalation. Resource limits enforced.'},
        'network_attacks':             {'tactics': 'Discovery, Lateral Movement',            'severity': 'Enables lateral movement in microservices. Container networks often lack segmentation.'},
        'capability_abuse':            {'tactics': 'Privilege Escalation, Defense Evasion', 'severity': 'CAP_SYS_ADMIN approx root access. Can mount host filesystems and bypass security controls.'},
        'image_registry':              {'tactics': 'Initial Access, Persistence',            'severity': 'Supply chain attack. Compromised images affect entire organization.'},
        'privileged_container_escape': {'tactics': 'Privilege Escalation',                  'severity': '--privileged flag disables all security. Full device access and host compromise.'},
    }
    FAILURE_REASONS = {
        'privileged_container_escape': 'Attack requires --privileged flag. Container is running in non-privileged mode (security control working as intended).',
        'docker_socket_escape':        'Docker socket not mounted in container. Security control preventing socket access.',
        'namespace_manipulation':      'Namespace isolation enforced. Cannot access host namespaces.',
        'capability_abuse':            'Dangerous capabilities not granted. Container running with minimal capabilities.',
        'resource_abuse':              'Resource limits enforced. cgroups preventing resource exhaustion.',
        'network_attacks':             'Network policies blocking lateral movement. Container network segmentation active.',
        'image_registry':              'Registry access denied. Authentication required for image operations.',
    }
    # feature_scores is the single source of truth — risk_score derived from sum
    feature_scores = {
        'docker_socket_escape':        {'Privilege Escalation': (100,0.25),'Host Access': (100,0.25),'Data Exfiltration': (85,0.20),'Lateral Movement': (70,0.15),'Persistence': (90,0.15)},
        'namespace_manipulation':      {'Privilege Escalation': (95,0.25), 'Host Access': (98,0.25), 'Data Exfiltration': (80,0.20),'Lateral Movement': (75,0.15),'Persistence': (60,0.15)},
        'resource_abuse':              {'Privilege Escalation': (30,0.25), 'Host Access': (25,0.25), 'Data Exfiltration': (40,0.20),'Lateral Movement': (35,0.15),'Persistence': (30,0.15)},
        'network_attacks':             {'Privilege Escalation': (50,0.25), 'Host Access': (45,0.25), 'Data Exfiltration': (90,0.20),'Lateral Movement': (95,0.15),'Persistence': (65,0.15)},
        'capability_abuse':            {'Privilege Escalation': (95,0.25), 'Host Access': (85,0.25), 'Data Exfiltration': (75,0.20),'Lateral Movement': (60,0.15),'Persistence': (80,0.15)},
        'image_registry':              {'Privilege Escalation': (80,0.25), 'Host Access': (70,0.25), 'Data Exfiltration': (95,0.20),'Lateral Movement': (75,0.15),'Persistence': (95,0.15)},
        'privileged_container_escape': {'Privilege Escalation': (100,0.25),'Host Access': (100,0.25),'Data Exfiltration': (95,0.20),'Lateral Movement': (85,0.15),'Persistence': (95,0.15)},
    }
    mitre_ids = {
        'docker_socket_escape':'T1611','privileged_container_escape':'T1611',
        'namespace_manipulation':'T1611','resource_abuse':'T1496',
        'network_attacks':'T1046','capability_abuse':'T1611','image_registry':'T1525',
    }
    impact_desc = {
        'docker_socket_escape':'Full host access via Docker daemon',
        'namespace_manipulation':'Host filesystem access via proc',
        'resource_abuse':'CPU/Memory/Disk exhaustion',
        'network_attacks':'Service discovery and enumeration',
        'capability_abuse':'Host filesystem mount capability',
        'image_registry':'Secret extraction from images',
        'privileged_container_escape':'Full device access via --privileged',
    }
    container_targets = {
        'docker_socket_escape':        [('attack-orchestrator','Docker Socket API','/var/run/docker.sock'),('vulnerable-web','Flask Application','Customer Portal Web Server'),('privileged-container','Privileged Runtime','Host PID namespace')],
        'namespace_manipulation':      [('attack-orchestrator','Linux Namespaces','/proc/1/root filesystem'),('attack-orchestrator','PID Namespace','Host process tree')],
        'resource_abuse':              [('attack-orchestrator','CPU Scheduler','Process spawning'),('attack-orchestrator','Memory Allocator','Heap memory'),('attack-orchestrator','Disk I/O','/tmp filesystem')],
        'network_attacks':             [('vulnerable-web','Flask Web Server','Port 80 HTTP service'),('vulnerable-api','Payment API','Port 5000 REST API'),('vulnerable-db','PostgreSQL Database','Port 5432 database service')],
        'capability_abuse':            [('attack-orchestrator','CAP_SYS_ADMIN','Mount syscall'),('attack-orchestrator','CAP_NET_ADMIN','Network configuration')],
        'image_registry':              [('attack-orchestrator','Docker Registry','Image layers'),('attack-orchestrator','Docker Config','~/.docker/config.json')],
        'privileged_container_escape': [('privileged-container','Privileged Runtime','Host device access')],
    }

    attacks = []
    if raw_attacks:
        for atk in raw_attacks:
            t = atk['attack_type']
            feats = feature_scores.get(t, {})
            score = round(sum(s * w for s, w in feats.values()), 1)
            level = 'CRITICAL' if score >= 80 else 'HIGH' if score >= 60 else 'MEDIUM' if score >= 40 else 'LOW'
            feats = feature_scores.get(t, {})
            attacks.append({
                'name': t.replace('_',' ').title(),
                'type': t,
                'status': atk['status'],
                'risk_score': score,
                'risk_level': level,
                'mitre_tactics': MITRE_MAPPINGS.get(t, {}).get('tactics', 'Unknown'),
                'severity_reason': MITRE_MAPPINGS.get(t, {}).get('severity', ''),
                'failure_reason': FAILURE_REASONS.get(t, '') if atk['status'] == 'failed' else '',
                'mitre_id': mitre_ids.get(t, 'T0000'),
                'ml_data': {
                    'score': score, 'level': level,
                    'features': [{'name': f, 'score': s, 'weight': w, 'contribution': round(s*w,1)} for f,(s,w) in feats.items()]
                },
                'count': atk.get('count', 1),
                'timestamp': atk.get('timestamp', ''),
            })

    total = len(attacks)
    successful = sum(1 for a in attacks if a['status'] == 'success')
    success_rate = round((successful / total * 100) if total > 0 else 0, 1)
    risk_dist = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for a in attacks:
        risk_dist[a['risk_level']] += 1

    # Pre-fetch all unique container metrics IN PARALLEL to avoid serial blocking
    unique_containers = set()
    for atk in attacks:
        for (cname, _, _) in container_targets.get(atk['type'], []):
            unique_containers.add(cname)

    threads = [threading.Thread(target=get_container_metrics, args=(c,)) for c in unique_containers]
    for t in threads: t.start()
    for t in threads: t.join(timeout=5)

    infrastructure = []
    for atk in attacks:
        for (cname, target, specific) in container_targets.get(atk['type'], []):
            m = get_container_metrics(cname)
            infrastructure.append({
                'attack_name': atk['name'],
                'container': cname,
                'target_component': target,
                'specific_target': specific,
                'impact_description': impact_desc.get(atk['type'], 'Security impact'),
                'metrics': m,
            })

    return jsonify({
        'attacks': attacks,
        'infrastructure': infrastructure,
        'total_attacks': total,
        'success_rate': success_rate,
        'risk_distribution': risk_dist,
        'last_update': datetime.now().strftime('%H:%M:%S'),
    })

@app.route('/api/attacks')
def api_attacks():
    """JSON API for the React dashboard"""
    raw_attacks = get_attack_metrics_from_container()
    if not raw_attacks:
        return jsonify({'attacks': [], 'metrics': {}})
    metrics = {}
    for name in ['attack-orchestrator','vulnerable-web','vulnerable-api','vulnerable-db','privileged-container']:
        m = get_container_metrics(name)
        if m:
            metrics[name] = m
    return jsonify({'attacks': raw_attacks, 'metrics': metrics})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🛡️  Container Security Dashboard")
    print("="*70)
    print("Dashboard: http://localhost:8888")
    print("Note: Running directly - changes reflect instantly!")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=8888, debug=True, use_reloader=True)