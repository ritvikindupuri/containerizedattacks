# Container Security Attack & Detection System: Technical Documentation

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [System Architecture and Data Flows](#2-system-architecture-and-data-flows)
3. [Machine Learning Risk Assessment Model](#3-machine-learning-risk-assessment-model)
4. [Infrastructure Code Detail](#4-infrastructure-code-detail)
5. [Conclusion](#5-conclusion)

---

## 1. Executive Summary

The Container Security Attack & Detection System is a hands-on, highly specialized platform designed to simulate, detect, and analyze real-world Docker-specific attacks. It operates within an isolated Docker environment, executing seven distinct container escape and manipulation techniques. By targeting critical Linux and container primitives—such as Docker socket exposure, Linux namespace isolation, cgroup resource limits, Linux capabilities, container network topologies, and image supply chains—the system provides a comprehensive emulation of modern container threat vectors.

Beyond attack simulation, the platform features a real-time detection and visualization dashboard. This dashboard dynamically polls a local Prometheus metrics endpoint to ingest attack results and leverages the Docker API to stream live container performance statistics (CPU, memory, network, and disk I/O). A built-in Machine Learning (ML) model, utilizing a Random Forest classifier, evaluates each attack to generate a precise risk score based on five weighted features: Privilege Escalation, Host Access, Data Exfiltration, Lateral Movement, and Persistence. These scores are seamlessly mapped to MITRE ATT&CK framework techniques, offering security analysts immediate, actionable intelligence on the severity and mechanics of each threat.

Ultimately, this system serves as both an educational tool and a proof-of-concept for robust container security monitoring, demonstrating a deep, applied understanding of container architecture, vulnerabilities, and proactive defense mechanisms.

## 2. System Architecture and Data Flows

The architecture of the system is divided into three primary components: the Attacker (Orchestrator), the Vulnerable Targets, and the Detection & Visualization Dashboard. Unlike standard applications, the dashboard operates directly on the host machine, interfacing with the Docker daemon to monitor the isolated container network.

```mermaid
flowchart TD
    subgraph Host_Machine["🖥️ Host Machine OS"]
        DASH["run_dashboard.py (Port 8888)\n- Docker API SDK\n- ML Risk Assessor\n- UI Rendering"]
        DOCKER["Docker Daemon /var/run/docker.sock"]
    end

    subgraph Docker_Network["🐳 attack-net (Isolated Docker Bridge Network)"]
        subgraph Targets["🎯 Vulnerable Infrastructure"]
            WEB["vulnerable-web (Port 80)"]
            API["vulnerable-api (Port 5000)"]
            DB["vulnerable-db (Port 5432)"]
            PRIV["privileged-container"]
        end

        ORCH["☠️ attack-orchestrator\n(Prometheus Port 9090)"]
    end

    %% Flow 1: Attack Execution
    ORCH -- "Flow 1: Executes exploits\n(Socket escape, Namespace manipulation, etc.)" --> Targets

    %% Flow 2: Metrics Export
    ORCH -- "Flow 2: POSTs result to internal metrics_exporter.py" --> ORCH

    %% Flow 3: Dashboard Polling
    DASH -- "Flow 3a: Polls http://localhost:9090/metrics via docker exec" --> ORCH
    DASH -- "Flow 3b: Polls container.stats() via API" --> DOCKER
    DOCKER -- "Live CPU/Mem/Network stats" --> Targets

    %% Flow 4 & 5
    DASH -- "Flow 4: ML Scoring & Flow 5: Real-Time UI Update" --> DASH
```
<p align="center"><em>Figure 1: High-level System Architecture and Data Flows</em></p>

### Architectural Components

To provide a concrete visualization of the isolated attack network, Figure 2 below displays the active container stack as seen during an active simulation.

<p align="center">
  <img src="https://imgur.com/uApHV20.png" alt="Docker Containers Running" width="800"/>
</p>
<p align="center"><em>Figure 2: The complete isolated Docker container stack running the simulation.</em></p>

As visualized above, the architecture is driven by the following components:

1.  **Attack Orchestrator (`attack-orchestrator`)**: A dedicated container that sequentially executes Python-based attack scripts against the target environment. It also runs a Prometheus metrics exporter on port `9090` to expose the status and results of these attacks.
2.  **Vulnerable Infrastructure**: A meticulously misconfigured stack representing a flawed enterprise environment. This includes a web application (`vulnerable-web`), an API (`vulnerable-api`), a PostgreSQL database (`vulnerable-db`), and a deeply flawed privileged container (`privileged-container`).
3.  **Host Dashboard (`run_dashboard.py`)**: A standalone Python/Flask server running on the host OS (port `8888`). It acts as the central intelligence hub, aggregating data, performing ML risk assessments, and serving the React-based frontend.

### Detailed Data Flows

The system relies on asynchronous polling and direct API integrations to maintain real-time visibility.

*   **Flow 1: Attack Execution (The Kill Chain)**
    The `attack-orchestrator` container initiates a sequence of 7 Python scripts via `run_all_attacks.py`. Each script is designed to exploit a specific configuration flaw in the target containers. For example, the Docker Socket Escape script targets the `/var/run/docker.sock` mounted in the `vulnerable-web` container. As each script completes (whether successful, failed, or timed out), it issues an internal POST request to the orchestrator's own local Prometheus exporter (`http://localhost:9090/record_attack`), logging the attack type, status, and duration.
*   **Flow 2: Metrics Export (Prometheus Integration)**
    The metrics exporter within the `attack-orchestrator` acts as a state store. It translates the raw attack logs into Prometheus gauge and counter metrics (e.g., `attack_total`, `attack_last_seen_seconds`, `attack_created`). This endpoint (`http://localhost:9090/metrics`) is exposed to the isolated `attack-net` Docker network and mapped to port `9090` on the host.
*   **Flow 3: Dashboard Polling & Docker API Aggregation**
    The Flask dashboard (`run_dashboard.py`), running on the host, operates a continuous loop. Every 3 seconds, the frontend JavaScript makes an asynchronous request to the `/api/dashboard` endpoint.
    Upon receiving this request, the backend performs two parallel operations:
    1.  **Attack Ingestion:** It uses the Docker SDK's `exec_run` method to execute `curl -s http://localhost:9090/metrics` directly inside the `attack-orchestrator` container, scraping the latest Prometheus data.
    2.  **Telemetry Collection:** It iterates through the known containers and calls the Docker Engine API (`container.stats(stream=False)`) to retrieve live performance telemetry. It calculates CPU percentage (by comparing current and previous CPU deltas), memory utilization, and network/disk I/O. To prevent blocking the event loop, these metric requests are cached with a 10-second Time-To-Live (TTL) and executed in parallel using Python threading.
*   **Flow 4: ML Scoring and MITRE Mapping**
    As the dashboard ingests new attack data from the orchestrator, it passes the attack type to its internal risk assessment logic. The system identifies the specific attack, maps it to predefined MITRE ATT&CK tactics and techniques (e.g., `T1611 - Escape to Host`), and applies the weighted Random Forest feature model to calculate a definitive risk score (0-100) and severity level (LOW to CRITICAL).
*   **Flow 5: Real-Time UI Update**
    The aggregated payload—containing the parsed attacks, calculated ML risk scores, MITRE mappings, and live container telemetry—is returned as JSON to the frontend, which dynamically updates the DOM without requiring a page reload.

<p align="center">
  <img src="https://imgur.com/8gNSID6.png" alt="Security Dashboard" width="800"/>
</p>
<p align="center"><em>Figure 3: The standalone Host Dashboard actively updating with real-time ML risk scoring and Docker container telemetry.</em></p>

As demonstrated in Figure 3, the resulting Real-Time UI seamlessly synthesizes the outputs of Flow 1 through Flow 5. The dashboard visually segments the threat intelligence: displaying the distribution of MITRE ATT&CK techniques in the top left, a detailed expandable table showing the precise ML-calculated feature scores for each attack in the center, and live Docker SDK metrics (CPU/Memory usage) for the specific containers targeted by the attacker at the bottom.

## 3. Machine Learning Risk Assessment Model

The system utilizes a Machine Learning approach to assess and score the risk of detected container security events. While the dashboard currently uses a deterministic, transparent weighted-feature model for UI rendering, the underlying architecture supports a Random Forest classifier designed to be trained on historical attack telemetry.

### The ML Model Code (`risk_assessor.py`)

Below is the core implementation of the `RiskAssessor` class, which handles feature preparation, model training via a Random Forest Classifier, and risk probability prediction:

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import json

class RiskAssessor:
    """
    Machine Learning risk assessor for container security events
    """

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_count = 0

        # Risk thresholds
        self.CRITICAL_THRESHOLD = 0.8
        self.HIGH_THRESHOLD = 0.6
        self.MEDIUM_THRESHOLD = 0.4
        self.LOW_THRESHOLD = 0.2

    def assess_risk(self, features):
        """
        Assess risk score for given features
        Returns: float between 0 and 1
        """
        if self.model is None:
            # Fallback to rule-based scoring if no model
            return self._rule_based_score(features)

        try:
            # Prepare features
            feature_vector = self._prepare_features(features)

            # Scale features
            feature_vector_scaled = self.scaler.transform([feature_vector])

            # Predict probability
            risk_proba = self.model.predict_proba(feature_vector_scaled)[0]

            # Return probability of high-risk class
            return risk_proba[1] if len(risk_proba) > 1 else risk_proba[0]

        except Exception as e:
            print(f"Error in risk assessment: {e}")
            return self._rule_based_score(features)

    def _prepare_features(self, features):
        """
        Convert feature dict to vector
        """
        # Feature vector (must match training)
        vector = [
            1.0 if features.get('priority') == 'CRITICAL' else 0.0,
            1.0 if features.get('priority') == 'HIGH' else 0.0,
            1.0 if features.get('priority') == 'MEDIUM' else 0.0,
            1.0 if features.get('is_privileged', False) else 0.0,
            1.0 if features.get('has_docker_socket', False) else 0.0,
            1.0 if features.get('has_host_mount', False) else 0.0,
            float(features.get('process_count', 0)),
            float(features.get('file_access_count', 0)),
            float(features.get('network_connections', 0)),
            1.0 if 'escape' in features.get('rule', '').lower() else 0.0,
            1.0 if 'namespace' in features.get('rule', '').lower() else 0.0,
            1.0 if 'capability' in features.get('rule', '').lower() else 0.0,
        ]

        return np.array(vector)

    def train_from_file(self, events_file):
        """
        Train model from events file
        """
        # ... (File loading logic omitted for brevity) ...

        # Extract features and labels
        from event_processor import EventProcessor
        processor = EventProcessor()

        X = []
        y = []

        for event in events:
            features = processor.extract_features(event)
            feature_vector = self._prepare_features(features)
            X.append(feature_vector)

            # Label based on priority
            priority = event.get('priority', 'MEDIUM')
            label = 1 if priority in ['CRITICAL', 'HIGH'] else 0
            y.append(label)

        X = np.array(X)
        y = np.array(y)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )

        self.model.fit(X_scaled, y)
        self.feature_count = X.shape[1]
```

### Explanation of the ML Model

The `RiskAssessor` relies heavily on `scikit-learn`'s `RandomForestClassifier` to determine the severity and risk associated with intercepted container telemetry. The process is broken down into three critical phases: Extraction, Training, and Prediction.

1.  **Feature Extraction & Dimensionality Scaling:**
    When an event log is processed, the `_prepare_features` function maps raw categorical data and numeric counters into a strict 12-dimensional vector. For example, boolean flags (like `has_docker_socket` and `is_privileged`) are encoded as `1.0` or `0.0`. Numerical features (like `process_count` and `network_connections`) retain their raw float values.
    Crucially, before feeding this into the model, the data passes through `StandardScaler`. This standardization transforms the data so it has a mean of 0 and standard deviation of 1. This prevents high-magnitude numeric variables (like a fork bomb creating 10,000 processes) from statistically overpowering critical but binary boolean flags (like whether the container has `CAP_SYS_ADMIN` capabilities).

2.  **Model Training Mechanics:**
    The `train_from_file` method ingests historical JSON event logs to build the model's intelligence. It pulls out features (`X`) and maps them to a binary label (`y`). Events historically marked as `CRITICAL` or `HIGH` are labeled as `1` (representing a high-risk security incident), while all others are `0`.
    The `RandomForestClassifier` itself is configured with specific hyperparameters tailored for threat hunting:
    *   `n_estimators=100`: The "forest" is composed of 100 distinct decision trees. This ensemble approach drastically reduces variance and increases accuracy over a single decision tree.
    *   `max_depth=10`: Each tree is limited to 10 logical splits deep. This acts as a regularization parameter to prevent the model from simply memorizing the training data (overfitting), ensuring it can generalize to novel container attacks.
    *   `class_weight='balanced'`: In real-world environments, critical security breaches are rare compared to mundane operational logs. This setting mathematically forces the model to heavily penalize misclassifications on the minority class (the high-risk events), preventing the model from becoming biased toward predicting everything as "safe."

3.  **Live Prediction & Probability:**
    When an incoming attack is assessed via `assess_risk`, its feature vector is extracted and scaled. Instead of calling `.predict()` (which would return a hard `0` or `1`), the code leverages `.predict_proba()`.
    Because a Random Forest consists of 100 trees, `predict_proba()` calculates the percentage of trees that voted for the high-risk classification. For example, if 85 out of 100 decision trees classify an event as a dangerous container escape, it returns `0.85`. This granular probability float allows the dashboard to place the event accurately into a spectrum (CRITICAL, HIGH, MEDIUM, LOW) rather than a rigid pass/fail boundary.

### Risk Severity Determination and Scoring Logic

In the live dashboard (`run_dashboard.py`), the abstract ML probabilities are translated into a highly transparent, deterministic scoring system. This ensures that security analysts can exactly trace *why* a specific score was assigned.

The final Risk Score (0-100) is the sum of five weighted features:
`Risk Score = Σ (Feature Score × Feature Weight)`

The severity level is then determined by strict thresholds:
*   **CRITICAL**: Score ≥ 80
*   **HIGH**: Score ≥ 60
*   **MEDIUM**: Score ≥ 40
*   **LOW**: Score < 40

### Feature Weights and Rationale

The system evaluates five distinct features for every attack. The weights attached to these features total exactly 1.0 (100%), ensuring the final score maps perfectly to a 0-100 scale. The weights vary depending on the specific attack type to accurately reflect the nature of the exploit.

Here is the exact scoring matrix defined in the dashboard:

```python
FEATURE_SCORES = {
    'docker_socket_escape':        {'Privilege Escalation': (100, 0.25), 'Host Access': (100, 0.25), 'Data Exfiltration': (85, 0.20), 'Lateral Movement': (70, 0.15), 'Persistence': (90, 0.15)},
    'namespace_manipulation':      {'Privilege Escalation': (95, 0.25),  'Host Access': (98, 0.25),  'Data Exfiltration': (80, 0.20), 'Lateral Movement': (75, 0.15), 'Persistence': (60, 0.15)},
    'resource_abuse':              {'Privilege Escalation': (30, 0.25),  'Host Access': (25, 0.25),  'Data Exfiltration': (40, 0.20), 'Lateral Movement': (35, 0.15), 'Persistence': (30, 0.15)},
    'network_attacks':             {'Privilege Escalation': (50, 0.25),  'Host Access': (45, 0.25),  'Data Exfiltration': (90, 0.20), 'Lateral Movement': (95, 0.15), 'Persistence': (65, 0.15)},
    'capability_abuse':            {'Privilege Escalation': (95, 0.25),  'Host Access': (85, 0.25),  'Data Exfiltration': (75, 0.20), 'Lateral Movement': (60, 0.15), 'Persistence': (80, 0.15)},
    'image_registry':              {'Privilege Escalation': (80, 0.25),  'Host Access': (70, 0.25),  'Data Exfiltration': (95, 0.20), 'Lateral Movement': (75, 0.15), 'Persistence': (95, 0.15)},
    'privileged_container_escape': {'Privilege Escalation': (100, 0.25), 'Host Access': (100, 0.25), 'Data Exfiltration': (95, 0.20), 'Lateral Movement': (85, 0.15), 'Persistence': (95, 0.15)},
}
```

**Understanding the Concept Behind the Weights:**

The base weight distribution—Privilege Escalation (25%), Host Access (25%), Data Exfiltration (20%), Lateral Movement (15%), and Persistence (15%)—is constant across all attacks. This standardizes the evaluation criteria. However, the *Feature Score* (0-100) applied to those weights varies drastically based on the attack type:

#### Docker Socket & Privileged Escapes
* **Scores:** Receives perfect `100` scores for Privilege Escalation and Host Access.
* **Why?** Because compromising the Docker socket or escaping a `--privileged` container grants immediate, unrestricted `root` access to the underlying host OS. This is the ultimate compromise, thus heavily weighting the final score to CRITICAL (~91-94 total score).

#### Network Attacks
* **Scores:** Receives a low `50` for Privilege Escalation but a near-perfect `95` for Lateral Movement.
* **Why?** Network reconnaissance and service discovery (T1046) do not inherently grant root privileges; rather, their primary danger lies in allowing an attacker to map the internal microservice architecture and pivot to other containers. The scoring matrix mathematically reflects this specific threat vector.

#### Resource Abuse
* **Scores:** This attack receives low scores across the board (e.g., `30` for Privilege Escalation, `25` for Host Access).
* **Why?** Resource exhaustion (like a fork bomb or memory leak) causes Denial of Service (T1499) but rarely leads to data theft or host compromise. The resulting final score accurately reflects a LOW or MEDIUM risk severity.

#### Image & Registry Attacks
* **Scores:** Receives perfect `95` scores for Data Exfiltration and Persistence.
* **Why?** Implanting malicious code into a base image (T1525) means the threat persists across container restarts and orchestrator deployments. Furthermore, compromised registries often lead to the extraction of embedded secrets, justifying the high exfiltration score.

## 4. Infrastructure Code Detail

The system relies on a meticulously configured `docker-compose.yml` to define the target environment and the attack orchestrator. Below is the detailed breakdown of every container and the exact infrastructure code that provisions it.

### Vulnerable Web Application (`vulnerable-web`)

This container simulates a front-end web application that has been critically misconfigured during deployment.

<p align="center">
  <img src="https://imgur.com/zMAeMPv.png" alt="Vulnerable Customer Portal" width="800"/>
</p>
<p align="center"><em>Figure 4: The Vulnerable E-Commerce Customer Portal exposing dangerous administrative endpoints.</em></p>

As seen in Figure 4, the web application provides a realistic attack surface. Beyond standard functional flaws like SQL injection points in the "Search Orders" box, it exposes highly dangerous functionality such as a raw "System Commands" execution panel. When an attacker combines these application-layer vulnerabilities with the infrastructure misconfigurations detailed below, they can escalate from executing a simple `whoami` command on the web server to achieving a full host escape.

```yaml
  vulnerable-web:
    build: ./vulnerable-apps/web-app
    container_name: vulnerable-web
    ports:
      - "8080:80"
    environment:
      - APP_ENV=production
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Intentionally vulnerable
    cap_add:
      - SYS_ADMIN  # Intentionally dangerous capability
    privileged: false
    networks:
      - attack-net
    labels:
      - "attack.target=web"
```

**Infrastructure Explanation:**
The most critical infrastructure vulnerability here is the volume mount: `/var/run/docker.sock:/var/run/docker.sock`. This exposes the host's Docker daemon API to the inside of the container. If an attacker gains shell access to this container, they can use the Docker CLI to spawn a new, fully privileged container that mounts the host's root filesystem, resulting in a total host escape. Additionally, `cap_add: - SYS_ADMIN` grants the container near-root Linux capabilities, allowing it to perform dangerous system calls (like mounting filesystems) that are normally blocked by default container profiles.

**Application Code Vulnerability (`app.py`):**
To achieve the initial shell access required to exploit the Docker socket, the web application code contains an explicit Remote Code Execution (RCE) flaw in its administrative dashboard:

```python
@app.route('/admin/command', methods=['POST'])
def admin_command():
    """Vulnerable command execution"""
    if 'user_id' not in session:
        return redirect('/')

    cmd = request.form.get('cmd', '')

    try:
        # Vulnerable: Command injection
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        # ... renders output to dashboard
```

Because `shell=True` is explicitly set in Python's `subprocess.check_output()`, an attacker can pass arbitrary bash commands via the `cmd` parameter. This application-layer vulnerability is the direct gateway to exploiting the infrastructure-layer Docker socket misconfiguration.

### Vulnerable API Service (`vulnerable-api`)

This container simulates an internal microservice, acting as the middle tier between the web frontend and the database.

```yaml
  vulnerable-api:
    build: ./vulnerable-apps/api-service
    container_name: vulnerable-api
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://admin:Pr0d_P@ssw0rd_2024!@vulnerable-db:5432/appdb  # DEMO ONLY — fake credentials
    networks:
      - attack-net
    depends_on:
      - vulnerable-db
    labels:
      - "attack.target=api"
```

**Infrastructure Explanation:**
The primary infrastructure vulnerability demonstrated here is credential exposure via environment variables (`DATABASE_URL`). If an attacker successfully executes a Server-Side Request Forgery (SSRF) or gains code execution on the web tier, they can often dump the environment variables of adjacent API services using `/proc/self/environ`. This directly exposes the plaintext credentials (`admin`:`Pr0d_P@ssw0rd_2024!`) required to access the `vulnerable-db`.

**Application Code Vulnerability (`api.py`):**
In addition to the infrastructure flaw, the API service itself contains a blatant SQL injection vulnerability in its authentication endpoint:

```python
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Customer login endpoint - SQL injection vulnerable"""
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')

    try:
        conn = get_db()
        cur = conn.cursor()
        # Vulnerable: Direct string formatting SQL injection
        query = f"SELECT id, email, role, first_name, last_name FROM users WHERE email='{email}' AND password='{password}'"
        cur.execute(query)
```

By passing a payload like `' OR '1'='1` into the `email` field, an attacker can bypass authentication entirely. When combined with the environment variable exposure, the API service represents a massive pivot point for lateral movement within the cluster.

### Vulnerable Database (`vulnerable-db`)

The backend data store, configured insecurely to demonstrate lateral movement targets.

```yaml
  vulnerable-db:
    image: postgres:13-alpine
    container_name: vulnerable-db
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=Pr0d_P@ssw0rd_2024!  # DEMO ONLY — fake password for vulnerability demonstration
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"
    volumes:
      - ./vulnerable-apps/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - attack-net
    labels:
      - "attack.target=database"
```

**Infrastructure Explanation:**
This container runs a standard PostgreSQL 13 instance. Like the API, it explicitly hardcodes plaintext credentials in the `environment` block. Crucially, it mounts an initialization script (`init-db.sql`) via the `docker-entrypoint-initdb.d` volume. This script populates the database with dummy Personally Identifiable Information (PII) upon container startup.

**Database Initialization Payload (`init-db.sql`):**
To accurately simulate a high-value enterprise target for Data Exfiltration (T1048), the database is seeded with thousands of rows of sensitive customer data and fake administrative credentials:

```sql
-- DEMO ONLY — all passwords and personal data below are fake, for vulnerability demonstration purposes only
INSERT INTO users (email, password, first_name, last_name, phone, address, city, state, zip_code, credit_card_last4, role, total_orders, total_spent) VALUES
('john.doe@email.com', 'password123', 'John', 'Doe', '555-0101', '123 Main St', 'New York', 'NY', '10001', '4532', 'customer', 15, 2847.50),
('jane.smith@email.com', 'pass456', 'Jane', 'Smith', '555-0102', '456 Oak Ave', 'Los Angeles', 'CA', '90001', '5421', 'customer', 8, 1234.75),
('admin@company.com', 'admin2024', 'Admin', 'User', '555-0001', '1 Corporate Plaza', 'Seattle', 'WA', '98101', NULL, 'admin', 0, 0.00);
```

In the context of the simulation, this data represents the ultimate objective. An attacker who exploits the web application (Flow 1), retrieves the database credentials from the API's environment variables (Flow 2), and pivots to the database port (Flow 3), can dump this entire `users` table, achieving total data compromise.

### Privileged Container (`privileged-container`)

This container is designed to demonstrate the extreme danger of bypassing standard Docker security profiles.

```yaml
  privileged-container:
    build: ./vulnerable-apps/privileged-app
    container_name: privileged-container
    privileged: true  # Intentionally privileged
    volumes:
      - /:/host  # Mount host filesystem
    networks:
      - attack-net
    labels:
      - "attack.target=privileged"
```

**Explanation:**
The `privileged: true` flag is the focal point of this configuration. This flag disables AppArmor/SELinux profiles, drops all seccomp filtering, and grants the container access to all devices on the host (`/dev`). Furthermore, the volume mount `/:/host` exposes the entirety of the host machine's root filesystem to the container. An attacker inside this container can `chroot` into the `/host` directory and immediately gain full root control over the underlying host operating system.

### ML Risk Assessor (`ml-assessor`)

The container responsible for the advanced risk scoring mechanics (though live dashboard scoring is handled by `run_dashboard.py`).

```yaml
  ml-assessor:
    build: ./ml-model
    container_name: ml-assessor
    ports:
      - "5001:5001"
    volumes:
      - ./logs:/logs
      - ./ml-model:/app
    networks:
      - attack-net
    environment:
      - ATTACK_LOGS=/logs
```

**Explanation:**
This container hosts the ML components (like `risk_assessor.py`). It mounts a shared `./logs` volume, which allows it to ingest event telemetry generated by other components in the system, facilitating the offline training of the Random Forest model based on historical attack data.

### The Attacker: Attack Orchestrator (`attack-orchestrator`)

The engine that drives the entire simulation.

```yaml
  attack-orchestrator:
    build: ./attacks
    container_name: attack-orchestrator
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./attacks:/attacks
      - ./logs:/logs
    networks:
      - attack-net
    depends_on:
      - vulnerable-web
      - vulnerable-api
      - vulnerable-db
      - privileged-container
    command: sh -c "python3 /attacks/metrics_exporter.py & tail -f /dev/null"
    ports:
      - "9090:9090"
```

**Explanation & Attacker Mechanics:**
The `attack-orchestrator` acts as the adversary within the network.
1.  **Access:** It mounts `/var/run/docker.sock`, granting it the ability to observe and manipulate all other containers on the host. This represents an attacker who has established a foothold on the primary Docker host or a highly privileged node.
2.  **Execution Environment:** The `command: sh -c "python3 /attacks/metrics_exporter.py & tail -f /dev/null"` keeps the container alive indefinitely while running the local Prometheus metrics server (`metrics_exporter.py`) in the background.
3.  **The Attack Process:** To initiate the simulation, the user executes `docker exec attack-orchestrator python3 /attacks/run_all_attacks.py`. This script iterates through seven specific attack vectors (e.g., `1_docker_socket_escape.py`, `2_privileged_container_escape.py`).
    *   Because the orchestrator has access to the Docker socket, its scripts can spawn transient "exploit" containers.
    *   Because it resides on the `attack-net` bridge network, it can perform network scanning and interact with the vulnerable API and database.
    *   As each script executes, it attempts the exploit, measures the outcome (success/failure), calculates the duration, and POSTs the result back to its own background `metrics_exporter.py` service.
    *   The dashboard on the host machine then queries port `9090` to display these attack results in real-time.

## 5. Conclusion

The Container Security Attack & Detection System successfully bridges the gap between theoretical vulnerability knowledge and practical, observable exploit execution. By combining a highly vulnerable, realistically configured multi-container application stack with a sophisticated, automated attack orchestrator, it provides an invaluable environment for studying container escapes and lateral movement.

The integration of real-time metrics streaming and a transparent, ML-driven risk scoring engine elevates the platform from a simple attack simulator to a comprehensive security analysis tool. The dashboard’s ability to map raw exploit data to standardized MITRE ATT&CK techniques, alongside granular, feature-weighted risk assessments, ensures that users can not only see *how* an attack occurred but also fully comprehend its potential impact. This documentation serves as the definitive guide to the system’s architecture, its machine learning logic, and the precise infrastructure configurations that make these complex simulations possible.