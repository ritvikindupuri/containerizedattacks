#!/usr/bin/env python3
"""
Attack Orchestrator - Runs all container-specific attacks sequentially
"""

import subprocess
import time
import sys
import os
import requests
import json

ATTACKS = [
    {
        'name': 'Docker Socket Escape',
        'script': '1_docker_socket_escape.py',
        'description': 'Exploits exposed Docker socket for container escape',
        'type': 'docker_socket_escape',
        'affected_containers': ['vulnerable-web', 'privileged-container']
    },
    {
        'name': 'Privileged Container Escape',
        'script': '2_privileged_container_escape.py',
        'description': 'Exploits privileged mode and cgroup manipulation',
        'type': 'privileged_container_escape',
        'affected_containers': ['privileged-container']
    },
    {
        'name': 'Namespace Manipulation',
        'script': '3_namespace_manipulation.py',
        'description': 'Breaks container isolation via namespace manipulation',
        'type': 'namespace_manipulation',
        'affected_containers': ['attack-orchestrator']
    },
    {
        'name': 'Resource Abuse',
        'script': '4_resource_abuse.py',
        'description': 'Exhausts container resources (CPU, memory, PIDs, disk)',
        'type': 'resource_abuse',
        'affected_containers': ['attack-orchestrator']
    },
    {
        'name': 'Container Network Attacks',
        'script': '5_container_network_attacks.py',
        'description': 'Lateral movement and network reconnaissance',
        'type': 'network_attacks',
        'affected_containers': ['vulnerable-web', 'vulnerable-api', 'vulnerable-db']
    },
    {
        'name': 'Capability Abuse',
        'script': '6_capability_abuse.py',
        'description': 'Exploits dangerous Linux capabilities',
        'type': 'capability_abuse',
        'affected_containers': ['attack-orchestrator']
    },
    {
        'name': 'Image & Registry Attacks',
        'script': '7_image_registry_attacks.py',
        'description': 'Supply chain attacks on images and registries',
        'type': 'image_registry',
        'affected_containers': ['attack-orchestrator']
    }
]

def record_attack_metrics(attack_info, success, duration):
    """Record attack metrics to the metrics exporter"""
    try:
        data = {
            'attack_type': attack_info['type'],
            'status': 'success' if success else 'failed',
            'duration': duration,
            'affected_containers': attack_info['affected_containers'] if success else []
        }
        
        response = requests.post(
            'http://localhost:9090/record_attack',
            json=data,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"[✓] Metrics recorded for {attack_info['name']}")
        else:
            print(f"[!] Failed to record metrics: {response.status_code}")
            
    except Exception as e:
        print(f"[!] Error recording metrics: {e}")

def print_banner():
    """Print attack orchestrator banner"""
    print()
    print("=" * 80)
    print(" " * 20 + "CONTAINER ATTACK ORCHESTRATOR")
    print("=" * 80)
    print()
    print("This orchestrator will execute all container-specific attacks sequentially.")
    print("Each attack targets vulnerabilities unique to containerized environments.")
    print()
    print(f"Total attacks: {len(ATTACKS)}")
    print()
    print("=" * 80)
    print()

def run_attack(attack_num, attack_info):
    """Run a single attack script"""
    print()
    print("=" * 80)
    print(f"ATTACK {attack_num}/{len(ATTACKS)}: {attack_info['name']}")
    print("=" * 80)
    print(f"Description: {attack_info['description']}")
    print(f"Script: {attack_info['script']}")
    print()
    print("Starting attack in 3 seconds...")
    time.sleep(3)
    print()
    
    # Run the attack script
    script_path = f"/attacks/{attack_info['script']}"
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=False,
            text=True,
            timeout=60  # 60 second timeout per attack
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        if success:
            status = "SUCCESS"
        else:
            status = "FAILED"
        
        print()
        print(f"Attack Status: {status}")
        print()
        
        # Record metrics
        record_attack_metrics(attack_info, success, duration)
        
        return success
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print()
        print("Attack Status: TIMEOUT (exceeded 60 seconds)")
        print()
        record_attack_metrics(attack_info, False, duration)
        return False
    except Exception as e:
        duration = time.time() - start_time
        print()
        print(f"Attack Status: ERROR - {e}")
        print()
        record_attack_metrics(attack_info, False, duration)
        return False

def print_summary(results):
    """Print summary of all attacks"""
    print()
    print("=" * 80)
    print(" " * 30 + "ATTACK SUMMARY")
    print("=" * 80)
    print()
    
    successful = sum(results.values())
    total = len(results)
    
    print(f"Total Attacks: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print()
    
    print("Individual Results:")
    print("-" * 80)
    
    for i, attack in enumerate(ATTACKS, 1):
        status = "✓ SUCCESS" if results.get(i, False) else "✗ FAILED"
        print(f"{i}. {attack['name']:<40} {status}")
    
    print("-" * 80)
    print()
    
    # Calculate success rate
    success_rate = (successful / total) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    
    print("=" * 80)
    print()
    print("All attacks completed. Check the dashboard for detection events:")
    print("  http://localhost:8888")
    print("  cat /logs/events.json")
    print()

def main():
    """Main orchestrator function"""
    print_banner()
    
    # Confirm execution
    print("WARNING: This will execute real container-specific attacks!")
    print("Only run this in isolated test environments.")
    print()
    
    # Check if running in container
    if not os.path.exists('/.dockerenv'):
        print("ERROR: This script must be run inside the attack-orchestrator container")
        print()
        print("Run: docker exec -it attack-orchestrator python3 /attacks/run_all_attacks.py")
        sys.exit(1)
    
    print("Starting attacks...")
    print()
    
    # Run all attacks
    results = {}
    
    for i, attack in enumerate(ATTACKS, 1):
        success = run_attack(i, attack)
        results[i] = success
        
        # Wait between attacks
        if i < len(ATTACKS):
            print(f"Waiting 5 seconds before next attack...")
            time.sleep(5)
    
    # Print summary
    print_summary(results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("Attack orchestration cancelled by user")
        print()
        sys.exit(1)
