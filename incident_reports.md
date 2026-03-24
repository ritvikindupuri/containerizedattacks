# Security Incident Report: INC-2024-03-22

**CONFIDENTIAL - INTERNAL SECURITY OPERATIONS USE ONLY**

| Field | Detail |
|---|---|
| **Incident ID** | INC-2024-03-22 |
| **Date of Report** | March 22, 2024 |
| **Analyst** | Lead Incident Responder |
| **Status** | **[OPEN - CRITICAL]** |
| **Affected Environment** | Production Container Cluster (`attack-net`) |

---

## 1. Executive Summary

At approximately 02:00 UTC, the Container Security Detection platform recorded a rapid succession of sophisticated container escape and manipulation attempts targeting the core microservice architecture. The platform detected 7 distinct attack vectors within a highly condensed timeframe. The attacker achieved an **85.7% success rate**, resulting in complete compromise of the underlying host operating system and unrestricted lateral movement across the internal Docker bridge network (`attack-net`).

The Machine Learning Risk Assessor flagged **5 Critical Risk** events and **1 High Risk** event. The primary entry point appears to have been an explicitly vulnerable web application mounting the host's Docker socket, which was subsequently weaponized to deploy an unauthorized, highly privileged container, granting the adversary root access to the host machine.

### Key Evidence: Dashboard Telemetry

The following snapshot from the Security Dashboard captures the state of the cluster immediately following the attack chain, explicitly detailing the MITRE ATT&CK techniques utilized, the ML-calculated risk scores, and the affected infrastructure.

<p align="center">
  <img src="https://imgur.com/8gNSID6.png" alt="Security Dashboard Evidence Snapshot" width="800"/>
</p>
<p align="center"><em>Exhibit A: Real-time telemetry capturing the 7 distinct attack vectors, their ML risk scores, and the resulting success status.</em></p>

---

## 2. Timeline of Events (Attack Chain)

Based on the Prometheus metrics ingested by the dashboard, the adversary executed a heavily automated, sequential "Kill Chain":

1. **[T1611 - Escape to Host] Docker Socket Escape (CRITICAL - 91%)**
   - **Status:** **SUCCESS**
   - **Details:** The adversary exploited a volume mount (`/var/run/docker.sock`) exposed to the `vulnerable-web` container. They utilized the Docker SDK API to spawn a new container mounting the host's root filesystem.
   - **Impact:** Immediate unrestricted `root` access to the underlying host OS.

2. **[T1611 / T1055] Namespace Manipulation (CRITICAL - 84.5%)**
   - **Status:** **SUCCESS**
   - **Details:** The attacker accessed `/proc/1/root` (the host filesystem) and utilized the `nsenter` utility to actively join host namespaces.
   - **Impact:** Broke PID, mount, and network isolation boundaries, effectively bypassing the container runtime sandbox.

3. **[T1611] Privileged Container Escape (CRITICAL - 96%)**
   - **Status:** **FAILED**
   - **Details:** An attempt was made to exploit the `privileged-container`. The ML model scored this as a 96% critical risk due to the `--privileged` flag disabling AppArmor and seccomp filters.
   - **Note:** While the specific payload recorded a failure in this instance, the container remains critically vulnerable to device and cgroup manipulation.

4. **[T1496] Resource Abuse (LOW - 31.5%)**
   - **Status:** **SUCCESS**
   - **Details:** A classic Denial of Service (DoS) attempt aiming to exhaust CPU, Memory, or PID limits.
   - **Impact:** Minimal. The ML model correctly downgraded this to a LOW risk severity, recognizing that while disruptive, it does not lead to privilege escalation or data exfiltration.

5. **[T1046] Network Attacks (HIGH - 65.8%)**
   - **Status:** **SUCCESS**
   - **Details:** Following the initial compromise, the attacker initiated aggressive network reconnaissance and service discovery across the `attack-net` bridge.
   - **Impact:** High probability of lateral movement. This allowed the attacker to map the internal architecture and locate the `vulnerable-api` and `vulnerable-db` services.

6. **[T1611] Capability Abuse (CRITICAL - 81%)**
   - **Status:** **SUCCESS**
   - **Details:** The attacker successfully exploited dangerously broad Linux capabilities (specifically `CAP_SYS_ADMIN` granted to `vulnerable-web`) to perform unauthorized filesystem mounts.
   - **Impact:** Secondary method of achieving host escape.

7. **[T1525] Image Registry Attack (CRITICAL - 82%)**
   - **Status:** **SUCCESS**
   - **Details:** A supply chain vector indicating that the attacker either pulled a malicious image directly from an untrusted registry or successfully extracted embedded secrets from the Docker configuration (`~/.docker/config.json`).
   - **Impact:** Initial Access and deep Persistence.

---

## 3. Impact Assessment

The attack chain resulted in a **Total Compromise** of both the containerized application stack and the underlying Docker host.

*   **Confidentiality:** The `vulnerable-db` PostgreSQL instance (Port 5432) was exposed to the attacker via lateral movement (Network Attacks) and environment variable extraction (`vulnerable-api`). All customer PII and administrative credentials must be considered compromised.
*   **Integrity:** The adversary achieved root access on the host OS via the Docker Socket Escape. They have the capability to alter logs, modify container configurations, and inject malicious code into subsequent image builds.
*   **Availability:** While the Resource Abuse (DoS) attempt scored low on risk, the attacker possesses the necessary host privileges to forcefully terminate any container or the Docker daemon itself.

---

## 4. Remediation & Recommendations

To contain this incident and secure the cluster against future threats, the following actions must be prioritized immediately:

### Immediate Containment Actions
1. **Isolate the Host:** Sever the compromised Docker host machine from the wider production network to halt lateral movement beyond the `attack-net` bridge.
2. **Revoke Credentials:** Immediately cycle all database credentials, specifically those hardcoded in the `vulnerable-api` environment variables (`Pr0d_P@ssw0rd_2024!`). Rotate all Docker Registry authentication tokens.

### Infrastructure Hardening (Short-Term)
1. **Remove Docker Socket Mounts:** Immediately remove the `-v /var/run/docker.sock:/var/run/docker.sock` volume mount from the `vulnerable-web` container in `docker-compose.yml`. Applications should never have direct access to the daemon API.
2. **Drop Dangerous Capabilities:** Remove `cap_add: - SYS_ADMIN` from the `vulnerable-web` configuration. Enforce a policy of least privilege using standard Docker security profiles.
3. **Disable Privileged Mode:** Remove `privileged: true` and the `/:/host` volume mount from the `privileged-container`. If specific device access is required, explicitly whitelist those devices using the `--device` flag instead.

### Architectural Improvements (Long-Term)
1. **Implement Network Segmentation:** Do not place all containers on a flat bridge network (`attack-net`). Create isolated networks for the web tier, API tier, and database tier to prevent trivial lateral movement.
2. **Secret Management:** Eliminate plaintext environment variables. Implement a dedicated secrets management solution (e.g., Docker Secrets, HashiCorp Vault) to inject database credentials securely at runtime.
3. **Resource Quotas:** Enforce strict memory and CPU limits (`deploy.resources.limits`) on all containers to mitigate Resource Abuse and Denial of Service attempts.