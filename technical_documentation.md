# Container Security Attack & Detection System: Technical Documentation

## 1. Executive Summary

The Container Security Attack & Detection System is a hands-on, highly specialized platform designed to simulate, detect, and analyze real-world Docker-specific attacks. It operates within an isolated Docker environment, executing seven distinct container escape and manipulation techniques. By targeting critical Linux and container primitives—such as Docker socket exposure, Linux namespace isolation, cgroup resource limits, Linux capabilities, container network topologies, and image supply chains—the system provides a comprehensive emulation of modern container threat vectors.

Beyond attack simulation, the platform features a real-time detection and visualization dashboard. This dashboard dynamically polls a local Prometheus metrics endpoint to ingest attack results and leverages the Docker API to stream live container performance statistics (CPU, memory, network, and disk I/O). A built-in Machine Learning (ML) model, utilizing a Random Forest classifier, evaluates each attack to generate a precise risk score based on five weighted features: Privilege Escalation, Host Access, Data Exfiltration, Lateral Movement, and Persistence. These scores are seamlessly mapped to MITRE ATT&CK framework techniques, offering security analysts immediate, actionable intelligence on the severity and mechanics of each threat.

Ultimately, this system serves as both an educational tool and a proof-of-concept for robust container security monitoring, demonstrating a deep, applied understanding of container architecture, vulnerabilities, and proactive defense mechanisms.

## 2. Conclusion

The Container Security Attack & Detection System successfully bridges the gap between theoretical vulnerability knowledge and practical, observable exploit execution. By combining a highly vulnerable, realistically configured multi-container application stack with a sophisticated, automated attack orchestrator, it provides an invaluable environment for studying container escapes and lateral movement.

The integration of real-time metrics streaming and a transparent, ML-driven risk scoring engine elevates the platform from a simple attack simulator to a comprehensive security analysis tool. The dashboard’s ability to map raw exploit data to standardized MITRE ATT&CK techniques, alongside granular, feature-weighted risk assessments, ensures that users can not only see *how* an attack occurred but also fully comprehend its potential impact. This documentation serves as the definitive guide to the system’s architecture, its machine learning logic, and the precise infrastructure configurations that make these complex simulations possible.

## 3. System Architecture and Data Flows

The architecture of the system is divided into three primary components: the Attacker (Orchestrator), the Vulnerable Targets, and the Detection & Visualization Dashboard. Unlike standard applications, the dashboard operates directly on the host machine, interfacing with the Docker daemon to monitor the isolated container network.

### Architectural Components

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

## 4. Machine Learning Risk Assessment Model

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

The `RiskAssessor` is built around `scikit-learn`'s `RandomForestClassifier`.

1.  **Feature Extraction & Scaling:** When an event is processed, `_prepare_features` translates categorical and numerical data (e.g., presence of the Docker socket, `process_count`, `network_connections`) into a normalized 12-dimensional numerical vector. The `StandardScaler` ensures that high-magnitude continuous variables (like process counts) do not disproportionately dominate boolean flags (like `is_privileged`).
2.  **Training:** The `train_from_file` method ingests historical JSON event logs. It extracts features (`X`) and assigns binary labels (`y`), where `CRITICAL` or `HIGH` priority events are labeled as `1` (high-risk), and others as `0`. The model is trained using 100 decision trees (`n_estimators=100`) with a maximum depth of 10 (`max_depth=10`) to prevent overfitting. `class_weight='balanced'` ensures the model remains accurate even if high-risk events are rare in the training data.
3.  **Prediction:** When assessing a live attack, `assess_risk` scales the incoming feature vector and uses `predict_proba`. Instead of returning a hard binary classification, it returns the probability (0.0 to 1.0) that the event belongs to the high-risk class.

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

*   **Docker Socket & Privileged Escapes**: These receive perfect `100` scores for Privilege Escalation and Host Access. **Why?** Because compromising the Docker socket or escaping a `--privileged` container grants immediate, unrestricted `root` access to the underlying host OS. This is the ultimate compromise, thus heavily weighting the final score to CRITICAL (~91-94 total score).
*   **Network Attacks**: This receives a low `50` for Privilege Escalation but a near-perfect `95` for Lateral Movement. **Why?** Network reconnaissance and service discovery (T1046) do not inherently grant root privileges; rather, their primary danger lies in allowing an attacker to map the internal microservice architecture and pivot to other containers. The scoring matrix mathematically reflects this specific threat vector.
*   **Resource Abuse**: This attack receives low scores across the board (e.g., `30` for Privilege Escalation, `25` for Host Access). **Why?** Resource exhaustion (like a fork bomb or memory leak) causes Denial of Service (T1499) but rarely leads to data theft or host compromise. The resulting final score accurately reflects a LOW or MEDIUM risk severity.
*   **Image & Registry Attacks**: Receives perfect `95` scores for Data Exfiltration and Persistence. **Why?** Implanting malicious code into a base image (T1525) means the threat persists across container restarts and orchestrator deployments. Furthermore, compromised registries often lead to the extraction of embedded secrets, justifying the high exfiltration score.

## 5. Infrastructure Code Detail

The system relies on a meticulously configured `docker-compose.yml` to define the target environment and the attack orchestrator. Below is the detailed breakdown of every container and the exact infrastructure code that provisions it.

### Vulnerable Web Application (`vulnerable-web`)

This container simulates a front-end web application that has been critically misconfigured during deployment.

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

**Explanation:**
The most critical vulnerability here is the volume mount: `/var/run/docker.sock:/var/run/docker.sock`. This exposes the host's Docker daemon API to the inside of the container. If an attacker gains shell access to this container, they can use the Docker CLI to spawn a new, fully privileged container that mounts the host's root filesystem, resulting in a total host compromise. Additionally, `cap_add: - SYS_ADMIN` grants the container near-root Linux capabilities, allowing it to perform dangerous system calls (like mounting filesystems) that are normally blocked by default container profiles.

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

**Explanation:**
The primary vulnerability demonstrated here is credential exposure via environment variables (`DATABASE_URL`). If an attacker successfully executes a Server-Side Request Forgery (SSRF) or gains code execution on the web tier, they can often dump the environment variables of adjacent API services. This exposes the plaintext credentials required to access the `vulnerable-db`. It sits on the same internal `attack-net` network, facilitating lateral movement.

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

**Explanation:**
This container runs a standard PostgreSQL 13 instance. Like the API, it explicitly hardcodes plaintext credentials in the `environment` block. It also mounts an initialization script (`init-db.sql`) to populate the database with dummy PII (Personally Identifiable Information). In the context of the simulation, this container represents the ultimate target for data exfiltration once an attacker has successfully pivoted through the network.

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