# Container Security Attack & Detection System

A hands-on container security platform that simulates real-world Docker-specific attacks, assesses risk using a machine learning model, and visualizes everything in a live analyst dashboard. Built to demonstrate deep understanding of container threat vectors, Linux primitives, and security tooling.

---

## Project Description

This system runs 7 container-specific attacks inside an isolated Docker environment ΓÇö targeting Docker socket exposure, Linux namespace isolation, cgroup resource limits, Linux capabilities, container network topology, image supply chains, and privileged container escape. Each attack is mapped to MITRE ATT&CK, scored by a Random Forest ML classifier, and surfaced in a real-time dashboard that pulls live metrics directly from the Docker daemon.

The dashboard is a standalone Python/Flask server that runs on your machine (not inside Docker), polls the attack orchestrator's Prometheus metrics endpoint every 3 seconds, and re-renders the UI without any page reload.

---

## Key Features

- **7 container-specific attacks** ΓÇö Docker socket escape, privileged container escape, namespace manipulation, resource abuse, network lateral movement, capability abuse, image/registry supply chain attack
- **Real-time dashboard** ΓÇö auto-refreshes every 3 seconds, zero page reloads, live Docker container metrics (CPU, memory, network, disk I/O)
- **ML risk scoring** ΓÇö Random Forest classifier scores each attack across 5 weighted features; contributions sum exactly to the displayed score
- **MITRE ATT&CK mapping** ΓÇö every attack linked to technique IDs (T1611, T1496, T1046, T1525, T1055, T1068) with direct links to attack.mitre.org
- **Expandable attack detail** ΓÇö click any row in the dashboard to see attack mechanics, MITRE mapping, and a full risk level breakdown with progress bars
- **Vulnerable enterprise environment** ΓÇö e-commerce web app, payment API, PostgreSQL database, and a privileged container as realistic targets

---

## System Architecture

<p align="center"><img src="https://i.imgur.com/Pk7ER0S.png" alt="System Architecture" width="800"/></p>

<p align="center"><em>Figure 1 - System Architecture</em></p>


**Layer 1 - User Interface:** A single security analyst accesses the dashboard via browser at `localhost:8888`. All interaction flows down through HTTP REST API calls.

**Layer 2 - Dashboard (Port 8888):** `run_dashboard.py` is a standalone Flask server running on your host machine. It provides real-time attack visualization, built-in ML risk scoring, MITRE ATT&CK mapping, and live container metrics (CPU, memory, network, disk I/O). The frontend polls `/api/dashboard` every 3 seconds and re-renders without a page reload.

**Layer 3 - Processing Layer:** The `attack-orchestrator` container (port 9090) is the simulated threat actor. It runs 7 container-specific attack scripts sequentially and exposes results via a Prometheus metrics exporter. Four attacks (Namespace Manipulation, Resource Abuse, Capability Abuse, Image/Registry) execute within the orchestrator itself. Three attacks (Docker Socket Escape, Privileged Container Escape, Network Attacks) reach out to the target containers below.

**Layer 4 - Target Environment:** Four intentionally misconfigured containers sit on the `172.20.0.0/16` isolated bridge network. `vulnerable-web` (port 8080) has the Docker socket mounted and `CAP_SYS_ADMIN` set. `vulnerable-api` (port 5000) exposes SQL injection and credential disclosure endpoints. `privileged-container` runs with `privileged: true` and the host filesystem mounted at `/host`. `vulnerable-db` (port 5432) is a PostgreSQL instance with plaintext passwords.

---
---

## Detection Walkthrough

The following is an end-to-end detection story for the Docker Socket Escape attack, the highest-severity attack in this lab.

---

### Stage 1 - Attack Execution

The attacker container runs `1_docker_socket_escape.py`. Because `vulnerable-web` has `/var/run/docker.sock` mounted as a volume, the script connects directly to the Docker daemon from inside the container and spawns a new privileged container with the host filesystem at `/host` -- a full container escape via the Docker API.

---

### Stage 2 - Telemetry Collection

On completion, `run_all_attacks.py` POSTs the result to the Prometheus metrics exporter on port 9090. Three metrics are recorded: `attack_total` (incremented), `attack_duration_seconds` (elapsed time), and `attack_last_seen_seconds` (Unix timestamp).

---

### Stage 3 - Detection and Alert

Every 3 seconds the dashboard polls `attack-orchestrator:9090/metrics`. The moment `docker_socket_escape` appears with `status=success`, it surfaces as CRITICAL in the Risk Assessment table.

| Feature | Score | Weight | Contribution |
|---|---|---|---|
| Privilege Escalation | 100 | 0.25 | 25.0 |
| Host Access | 100 | 0.25 | 25.0 |
| Data Exfiltration | 85 | 0.20 | 17.0 |
| Lateral Movement | 70 | 0.15 | 10.5 |
| Persistence | 90 | 0.15 | 13.5 |
| **Total** | | | **91.0 / 100 - CRITICAL** |

---

### Stage 4 - MITRE ATT&CK Mapping

Automatically mapped to **T1611 - Escape to Host** (Privilege Escalation, Defense Evasion). The dashboard expand panel links directly to `https://attack.mitre.org/techniques/T1611/` for immediate technique cross-reference.

---

### Stage 5 - Analyst Response

1. **Immediate**: Remove `/var/run/docker.sock` volume mount from `vulnerable-web`.
2. **Audit**: Run `docker inspect --format='{{.HostConfig.Binds}}' ` to find all socket mounts.
3. **Hardening**: Enforce admission policy (OPA/Gatekeeper) blocking container specs with Docker socket mounts.
4. **Detection rule**: Alert on any process inside a container opening `/var/run/docker.sock` -- this should never occur in production.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard server | Python 3, Flask, flask-cors |
| Docker integration | Docker SDK for Python (`docker`) |
| ML model | scikit-learn (Random Forest), numpy, pandas |
| Metrics | Prometheus client (prometheus-client) |
| Attack scripts | Python 3, requests, psutil |
| Vulnerable apps | Flask (web + API), PostgreSQL 13 |
| Infrastructure | Docker Desktop, Docker Compose |
| Frontend | Vanilla JS, SVG (donut chart), HTML/CSS |

---

## Setup Instructions

### Prerequisites

**1. Docker Desktop**

Download and install Docker Desktop for your OS:
- Windows / macOS: https://www.docker.com/products/docker-desktop
- Linux: `curl -fsSL https://get.docker.com | sh`

After installing, open Docker Desktop and make sure it is **running** (whale icon in system tray / menu bar).

Verify:
```bash
docker --version
docker compose version
```

Both commands must return a version number. If `docker compose` fails, you may have an older install ΓÇö use `docker-compose` (with hyphen) instead throughout these instructions.

**2. Python 3.9+**

The dashboard runs directly on your machine, not inside Docker.

- Windows: https://www.python.org/downloads/ ΓÇö check "Add Python to PATH" during install
- macOS: `brew install python` or download from python.org
- Linux: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

Verify:
```bash
python --version   # or python3 --version
pip --version      # or pip3 --version
```

**3. Git**

- Windows: https://git-scm.com/download/win
- macOS: `xcode-select --install`
- Linux: `sudo apt install git`

---

### Step 1 ΓÇö Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
```

Replace `<repository-url>` with the actual GitHub URL and `<repository-folder>` with the folder name it clones into.

---

### Step 2 ΓÇö Install dashboard Python dependencies

The dashboard (`run_dashboard.py`) runs on your host machine and needs three packages:

```bash
pip install flask flask-cors docker
```

If `pip` is not found, try `pip3`. On Linux you may need `pip3 install --user flask flask-cors docker`.

Verify the install worked:
```bash
python -c "import flask, flask_cors, docker; print('OK')"
```

You should see `OK`. If you see an import error, re-run the pip install command.

---

### Step 3 ΓÇö Build and start all Docker containers

This builds all container images and starts them in the background. The first run downloads base images and installs dependencies ΓÇö expect 5ΓÇô10 minutes.

```bash
docker compose up -d --build
```

> **Windows users:** Run this in PowerShell or Command Prompt, not Git Bash (Docker socket path issues).

Wait for the command to finish. You should see output ending with lines like:
```
Γ£ö Container vulnerable-db        Started
Γ£ö Container vulnerable-web       Started
Γ£ö Container vulnerable-api       Started
Γ£ö Container privileged-container Started
Γ£ö Container attack-orchestrator  Started
Γ£ö Container ml-assessor          Started
```

Verify all 6 containers are running:
```bash
docker ps
```

You should see all 6 containers with status `Up`. If any show `Exited`, see Troubleshooting below.

---

### Step 4 ΓÇö Wait for services to initialize

The attack orchestrator and ML assessor need ~15 seconds to fully start their internal servers.

```bash
# Windows PowerShell:
Start-Sleep -Seconds 20

# macOS / Linux:
sleep 20
```

Confirm the metrics endpoint is live:
```bash
# Windows PowerShell:
Invoke-WebRequest -Uri http://localhost:9090/health -UseBasicParsing

# macOS / Linux:
curl http://localhost:9090/health
```

Expected response: `{"status": "healthy"}`

If you get a connection error, wait another 10 seconds and try again.

---

### Step 5 ΓÇö Start the dashboard

Open a terminal in the project root folder and run:

```bash
python run_dashboard.py
```

> On macOS/Linux use `python3 run_dashboard.py` if `python` points to Python 2.

You should see:
```
Γ£ô Connected to Docker Desktop
======================================================================
≡ƒ¢í∩╕Å  Container Security Dashboard
======================================================================
Dashboard: http://localhost:8888
```

Leave this terminal open ΓÇö the dashboard server must keep running.

Open your browser and go to: **http://localhost:8888**

You will see the dashboard with empty tables and dashes in the stat cards. That is correct ΓÇö no attacks have run yet.

---

### Step 6 ΓÇö Run the attack simulation

Open a **second terminal** (keep the dashboard terminal running) and execute:

```bash
docker exec attack-orchestrator python3 /attacks/run_all_attacks.py
```

This runs all 7 attacks sequentially inside the `attack-orchestrator` container. Each attack prints detailed output. The full simulation takes approximately 2ΓÇô3 minutes.

You will see output like:
```
CONTAINER ATTACK: Docker Socket Escape
...
ATTACK SUCCESSFUL: Container Escape via Docker Socket
...
[Γ£ô] Metrics recorded for Docker Socket Escape
```

While the attacks run, switch back to your browser at **http://localhost:8888** ΓÇö the dashboard will populate with data within 3 seconds of each attack completing, automatically, with no refresh needed.

---

### Step 7 ΓÇö Explore the dashboard

Once all attacks complete you will see:

- **Stats bar** ΓÇö total attack types, success rate, critical/high risk counts
- **Attack Distribution** ΓÇö donut chart with MITRE IDs on each slice
- **Risk Assessment table** ΓÇö click any row to expand a 3-column detail panel showing attack mechanics, MITRE ATT&CK links, and the ML risk score breakdown
- **Affected Infrastructure table** ΓÇö live CPU/memory metrics per container, with `i` buttons for impact details
- **Footer** ΓÇö live dot + last updated timestamp confirming auto-refresh is active

---

### Re-running attacks

The Prometheus counters live in the `attack-orchestrator` container's memory. To reset to zero and run a fresh simulation:

```bash
# Restart the container (resets all counters)
docker compose restart attack-orchestrator

# Wait ~15 seconds for the metrics server to come back up
# Then run attacks again:
docker exec attack-orchestrator python3 /attacks/run_all_attacks.py
```

---

### Running individual attacks

```bash
docker exec attack-orchestrator python3 /attacks/1_docker_socket_escape.py
docker exec attack-orchestrator python3 /attacks/2_privileged_container_escape.py
docker exec attack-orchestrator python3 /attacks/3_namespace_manipulation.py
docker exec attack-orchestrator python3 /attacks/4_resource_abuse.py
docker exec attack-orchestrator python3 /attacks/5_container_network_attacks.py
docker exec attack-orchestrator python3 /attacks/6_capability_abuse.py
docker exec attack-orchestrator python3 /attacks/7_image_registry_attacks.py
```

---

### Stopping everything

```bash
# Stop all containers (preserves data)
docker compose down

# Stop and wipe all container data
docker compose down -v
```

To stop the dashboard, press `Ctrl+C` in the terminal running `run_dashboard.py`.

---

## Troubleshooting

**Dashboard shows "No attacks detected yet"**

The dashboard is running but no attacks have been recorded. Run Step 6.

**`docker exec` says container not found**

The container may have exited. Check:
```bash
docker ps -a
```
If `attack-orchestrator` shows `Exited`, restart it:
```bash
docker compose up -d attack-orchestrator
```
Wait 15 seconds, then re-run the attacks.

**Port already in use (8888, 9090, 5000, 5001, 8080, 5432)**

Another process is using that port. Find and stop it:
```bash
# Windows PowerShell:
Get-NetTCPConnection -LocalPort 8888 | Select-Object OwningProcess

# macOS / Linux:
lsof -i :8888
```
Or change the conflicting port mapping in `docker-compose.yml` (left side of `host:container`).

**`pip install` fails or packages not found**

Try:
```bash
python -m pip install flask flask-cors docker
```

**Docker Desktop not connecting**

Make sure Docker Desktop is open and the whale icon shows "Docker Desktop is running". On Windows, ensure WSL 2 backend is enabled in Docker Desktop settings.

**`docker compose` not found**

Try `docker-compose` (with hyphen). If neither works, reinstall Docker Desktop.

---

## Security Notice

This project contains intentionally vulnerable containers and executes real container escape techniques. Run only in an isolated local environment. Never deploy on a production system or a network with sensitive data.