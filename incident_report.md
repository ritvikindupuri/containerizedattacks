# INCIDENT REPORT: INC-2024-001
**Status:** OPEN
**Severity:** CRITICAL
**Date:** 2024-05-24
**Reported By:** Security Operations Center (SOC) Analyst

---

## 1. Executive Summary

<p align="center">
  <img src="https://imgur.com/72sw3lt.png" alt="Security Dashboard Capture" width="1000"/>
</p>
<p align="center"><em>Figure 1: Security Dashboard capture during the incident</em></p>

At approximately 14:00 UTC, the Container Security Attack & Detection System detected a coordinated, multi-stage attack against the isolated `attack-net` container network. The threat actor successfully executed **6 out of 7** attempted container-specific attacks, achieving an **85.7% success rate**. The attack campaign resulted in **5 Critical Risk** events and **1 High Risk** event. The primary objectives of the attack appeared to be comprehensive host compromise, privilege escalation, and lateral movement across the containerized infrastructure.

The most critical successful exploits included a **Docker Socket Escape (91% ML Score)** and a **Privileged Container Escape (96% ML Score)**, both of which granted the attacker full, unmitigated `root` access to the underlying Docker host. Immediate remediation and isolation of the affected infrastructure are required.

---

## 2. Attack Campaign Overview

*   **Total Attack Types Detected:** 7
*   **Attack Success Rate:** 85.7% (6 Successful, 1 Failed)
*   **Risk Distribution:**
    *   **CRITICAL:** 5 events
    *   **HIGH:** 1 event
    *   **LOW:** 1 event (Failed attempt)

### 2.1 Attack Distribution (MITRE ATT&CK Mapping)

The attack vectors were evenly distributed across 7 distinct techniques, representing 14.3% of the total campaign volume each. The primary MITRE ATT&CK techniques observed were:
*   **T1611 (Escape to Host):** Docker Socket Escape, Namespace Manipulation, Privileged Container Escape, Capability Abuse.
*   **T1496 (Resource Hijacking):** Resource Abuse.
*   **T1046 (Network Service Discovery):** Network Attacks.
*   **T1525 (Implant Internal Image):** Image Registry.

---

## 3. Detailed Incident Assessment & ML Risk Scoring

The Machine Learning (ML) Risk Assessor evaluated the telemetry for each attack phase. The following details the specifics of the successful and failed exploits based on the generated risk scores.

### 3.1 CRITICAL Findings

#### 3.1.1 Privileged Container Escape (Failed - Simulated)
*   **Status:** FAILED
*   **Risk Level:** CRITICAL
*   **ML Score:** 96%
*   **MITRE Tactics:** Privilege Escalation
*   **Analyst Note:** While this specific attack was marked as FAILED in the dashboard, its potential impact (96% risk score) makes it the most dangerous vector attempted. The attack targets a container running with the `--privileged` flag, attempting to gain full device access and compromise the host. The failure indicates a potential misconfiguration in the attacker's payload or a successful compensatory control, but the attempt itself is highly alarming.

#### 3.1.2 Docker Socket Escape (Successful)
*   **Status:** SUCCESS
*   **Risk Level:** CRITICAL
*   **ML Score:** 91%
*   **MITRE Tactics:** Privilege Escalation, Defense Evasion
*   **Target Infrastructure:** `attack-orchestrator`, `vulnerable-web`, `privileged-container`
*   **Impact:** Full host access via Docker daemon.
*   **Analyst Note:** The attacker successfully exploited an exposed `/var/run/docker.sock` API endpoint. This allowed the attacker to bypass all container isolation and spawn new, privileged containers on the host, granting them effective `root` privileges on the underlying operating system. This is a total compromise of the host node.

#### 3.1.3 Namespace Manipulation (Successful)
*   **Status:** SUCCESS
*   **Risk Level:** CRITICAL
*   **ML Score:** 84.5%
*   **MITRE Tactics:** Privilege Escalation, Defense Evasion
*   **Attack Detail:** Exploits Linux namespace isolation by accessing `/proc/1/root` (host filesystem) and using `nsenter` to join host namespaces. Breaks PID, mount, and network isolation.
*   **MITRE ATT&CK Mapping:** T1611 / T1055 (Escape to Host / Process Injection)
*   **Risk Level Determination (Feature Weights):**
    *   Privilege Escalation: Score 95% (+23.8)
    *   Host Access: Score 98% (+24.5)
    *   Data Exfiltration: Score 80% (+16.0)
    *   Lateral Movement: Score 75% (+11.2)
    *   Persistence: Score 60% (+9.0)
    *   *Sum of contributions: 84.5% (CRITICAL = score ≥ 80%)*
*   **Analyst Note:** Following the initial foothold, the attacker successfully manipulated Linux namespaces to further embed themselves into the host OS, breaking fundamental container isolation boundaries.

#### 3.1.4 Image Registry Attack (Successful)
*   **Status:** SUCCESS
*   **Risk Level:** CRITICAL
*   **ML Score:** 82%
*   **MITRE Tactics:** Initial Access, Persistence
*   **Analyst Note:** The attacker successfully compromised the image registry or image deployment pipeline. This represents a severe supply chain vulnerability, allowing the attacker to implant malicious code or extract embedded secrets (Data Exfiltration scored highly for this vector), ensuring long-term persistence across the environment.

#### 3.1.5 Capability Abuse (Successful)
*   **Status:** SUCCESS
*   **Risk Level:** CRITICAL
*   **ML Score:** 81%
*   **MITRE Tactics:** Privilege Escalation, Defense Evasion
*   **Analyst Note:** The attacker successfully abused excessive Linux capabilities (likely `CAP_SYS_ADMIN`) granted to a container. This allowed them to bypass standard security profiles (AppArmor/SELinux) and execute dangerous system calls, facilitating further host compromise.

### 3.2 HIGH Findings

#### 3.2.1 Network Attacks (Successful)
*   **Status:** SUCCESS
*   **Risk Level:** HIGH
*   **ML Score:** 65.8%
*   **MITRE Tactics:** Discovery, Lateral Movement
*   **Analyst Note:** The attacker successfully executed network discovery and scanning operations within the isolated container network. This facilitated lateral movement, allowing the attacker to map out internal microservices (e.g., APIs, databases) and identify vulnerable secondary targets.

### 3.3 LOW Findings

#### 3.3.1 Resource Abuse (Successful)
*   **Status:** SUCCESS
*   **Risk Level:** LOW
*   **ML Score:** 31.5%
*   **MITRE Tactics:** Impact
*   **Analyst Note:** The attacker successfully executed a resource exhaustion attack (e.g., fork bomb, memory leak) against a target container. While successful in causing localized disruption (Denial of Service), the ML model correctly assessed this as a LOW risk (31.5%) because it does not inherently lead to privilege escalation, data exfiltration, or host compromise.

---

## 4. Affected Infrastructure & Live Telemetry

During the peak of the attack, the dashboard captured live telemetry from the affected infrastructure, specifically focusing on the targets of the **Docker Socket Escape**:

| Attack | Container | Target | Impact | CPU | Memory |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Docker Socket Escape | `attack-orchestrator` | **Docker Socket API** (`/var/run/docker.sock`) | Full host access via Docker daemon | 0.44% | 32.11MB (0.2%) |
| Docker Socket Escape | `vulnerable-web` | **Flask Application** (Customer Portal Web Server) | Full host access via Docker daemon | 0% | 34.34MB (0.22%) |
| Docker Socket Escape | `privileged-container` | **Privileged Runtime** (Host PID namespace) | Full host access via Docker daemon | 0% | 3.69MB (0.02%) |

**Telemetry Analysis:** The relatively low CPU and Memory utilization during the active escape indicates that the exploits were highly efficient and did not rely on brute-force or resource-intensive methods. The host was compromised silently and swiftly.

---

## 5. Containment and Remediation Recommendations

Immediate action is required to secure the environment:

1.  **Immediate Containment (Host Level):** The underlying Docker host is considered completely compromised due to the successful Docker Socket and Namespace Manipulation escapes. The host must be immediately quarantined from the wider corporate network to prevent further lateral movement.
2.  **Configuration Audit (Docker Socket):** Immediately audit all container deployments for improper volume mounts of `/var/run/docker.sock`. Remove this mount from `vulnerable-web` and any other non-essential containers.
3.  **Configuration Audit (Privileged Containers):** Identify and terminate any containers running with the `--privileged` flag or excessive capabilities (e.g., `CAP_SYS_ADMIN`) unless strictly necessary and documented.
4.  **Enforce Namespace Isolation:** Ensure that containers are not launched with `--pid=host` or `--net=host` unless explicitly required.
5.  **Network Segmentation:** Implement strict network policies to prevent arbitrary lateral movement between microservices (addressing the successful Network Attacks).
6.  **Registry Audit:** Investigate the Image Registry attack. Audit registry access logs, scan all current base images for implanted malware or exposed secrets, and rotate any potentially compromised credentials.

**Analyst Signature:** _______________
**Date/Time:** 2024-05-24 14:30 UTC