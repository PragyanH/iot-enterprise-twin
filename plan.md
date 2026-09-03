# AEGIS-TWIN — FINAL HACKATHON FINALS PLAN

**Status:** FROZEN MASTER PLAN  
**Purpose:** Single source of truth for the finals build  
**Primary goal:** A beautiful, technically defensible, deterministic end-to-end IoT cyber-resilience demonstration that cannot fail under normal judging conditions.

---

# 1. Final Product Definition

**Aegis-Twin is an explainable cyber-resilience digital twin for enterprise IoT fleets. It continuously models expected device behavior, detects known and unknown anomalies, explains the mathematical evidence behind every decision, maps recognized behavior to MITRE ATT&CK, captures forensic evidence, applies controlled remediation, and verifies that the protected device returns to a trusted state.**

The product story is:

```text
OBSERVE
→ DETECT
→ EXPLAIN
→ PROVE
→ CAPTURE FORENSICS
→ REMEDIATE
→ RECOVER
```

The finals should never feel like “we trained a classifier and made a dashboard.”

It should feel like an **enterprise IoT Security Operations platform with a real physical cyber-resilience loop**.

---

# 2. Non-Negotiable Finals Story

The central live demonstration must always follow this exact sequence:

```text
Raspberry Pi connected
↓
Live telemetry begins
↓
Trust = 95–100
↓
State = HEALTHY
↓
Controlled SYN attack starts from VMware VM
↓
Real packet behavior changes
↓
Aegis detects divergence
↓
HEALTHY → SUSPICIOUS → ATTACK
↓
Trust drops below 30
↓
Known attack is classified
↓
MITRE ATT&CK mapping appears
↓
Forensic report is created
↓
Operator clicks CONTAIN & REMEDIATE
↓
Aegis isolates the malicious communication path if real isolation is stable
OR
automatically stops the registered VM attack as guaranteed fallback
↓
Pi traffic returns to baseline
↓
State = RECOVERING
↓
Clean windows are verified
↓
Trust returns above 95
↓
State = HEALTHY
↓
Digital twin re-synchronized
```

This sequence is more important than adding extra attack types.

---

# 3. Frozen Technology Stack

## Frontend

- React / Next.js
- Tailwind
- Existing Aegis visual theme
- SSE for live trust/state updates

## Backend

- FastAPI
- Existing telemetry-window API
- Existing trust/state engine
- Existing forensic report pipeline
- Existing allowlisted remediation controller

## Model / Intelligence

- XGBoost — known attack classification
- LSTM-VAE — temporal behavioral anomaly detection
- Jensen-Shannon Divergence — distribution drift
- YAML attack/security rules — deterministic known signatures
- Aegis Trust Composer — final operational trust/state

## Physical endpoint

- Raspberry Pi
- Device ID: `PI-001`

## Host

- Windows laptop

## Attack environment

- VMware Linux VM
- **VMware is used only for the controlled attack and attack-controller fallback**

## Live Windows network capture

- **Npcap + TShark**
- Custom Python telemetry adapter:
  - `scripts/tshark_live.py`

## Attack generation

- **Scapy inside the VMware VM**
- Registered controlled job:
  - `pi-syn-demo`

## Keep but remove from finals-critical path

- Zeek:
  - alternative Linux sensor
  - replay/offline/architecture capability
- NFStream:
  - optional offline ML / research feature analysis
- Suricata:
  - not required for finals

---

# 4. Why This Stack Is Frozen

The critical path must contain as few moving components as possible.

Final live dependency chain:

```text
Pi
↓
Windows USB/Ethernet network interface
↓
Npcap
↓
TShark
↓
tshark_live.py
↓
FastAPI
↓
Aegis Hybrid Engine
↓
SSE
↓
React UI
```

The VM does not own telemetry.

The VM does not own the backend.

The VM does not own the frontend.

The VM exists only to generate the controlled malicious traffic and expose the registered attack-controller endpoint.

Therefore a VMware problem cannot simultaneously kill detection, telemetry, backend and UI.

---

# 5. Final Network Architecture

Recommended physical/logical topology:

```text
                              WINDOWS HOST
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  React / Next.js                                              │
│      │                                                        │
│      ▼                                                        │
│  FastAPI                                                      │
│      │                                                        │
│      ▼                                                        │
│  Aegis Trust / Detection Engine                               │
│      ▲                                                        │
│      │ normalized 1-second telemetry                          │
│      │                                                        │
│  tshark_live.py                                               │
│      ▲                                                        │
│      │                                                        │
│  TShark + Npcap                                               │
│      ▲                                                        │
│      │                                                        │
│  Raspberry Pi USB Ethernet / isolated adapter                 │
│      │                                                        │
│      ├──────────────────────────────┐                         │
│      │                              │                         │
│      ▼                              ▼                         │
│  Raspberry Pi                  VMware Linux VM                │
│  PI-001                        controlled attacker             │
│                                  │                            │
│                                  └─ Scapy SYN scenario         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

# 6. VMware NIC Design

Use **two VM NICs** if possible.

## NIC 1 — Management

Purpose:

```text
Windows FastAPI
↔
VM Attack Controller
```

Recommended:

```text
Host-only network
```

This path should remain stable even while the attack network is under load.

## NIC 2 — Attack

Purpose:

```text
VM
→
Raspberry Pi
```

Bind this adapter specifically to the Windows Pi network interface.

Do not rely on VMware automatic bridging for the final demo if a specific adapter can be selected.

This separates:

```text
ATTACK PLANE
```

from:

```text
MANAGEMENT PLANE
```

which is a strong architecture decision and a strong judge explanation.

---

# 7. Raspberry Pi Connection

The Pi connects directly to Windows through a network-capable USB/Ethernet path.

Preferred:

- existing working USB Ethernet/RNDIS setup;
- USB Ethernet gadget mode;
- USB-to-Ethernet;
- direct Ethernet if needed.

Do **not** use a serial-only USB connection for the network-attack demo.

Use fixed addresses where practical.

Example conceptual layout:

```text
Windows Pi adapter
192.168.56.1

VM attack-side NIC
192.168.56.10

Raspberry Pi
192.168.56.20
```

Management plane can use a different host-only subnet.

Do not make the finals depend on:

- public Wi-Fi;
- campus DHCP;
- Internet access;
- unpredictable router configuration.

---

# 8. Primary Physical Attack

## Final hero attack

**SYN Flood**

MITRE ATT&CK:

```text
T1498.001
Direct Network Flood
```

This is the only attack that must work physically during the final presentation.

Why it is ideal:

- current Pi telemetry already contains the necessary features;
- current backend/tests already target this behavior;
- the attack produces clear visual changes;
- deterministic rules work extremely well;
- supervised classification works extremely well;
- remediation is easy to demonstrate;
- the trust score can be calibrated reliably below 30.

---

# 9. Known Attack Catalogue

Final supervised known classes:

```text
0 = NORMAL
1 = SYN FLOOD
2 = PORT SCAN
3 = SSH BRUTE FORCE
```

Physical hero:

```text
SYN FLOOD
```

Additional known attacks can be:

```text
replay
simulation
or physical only if already completely stable
```

Do not add another physical attack merely for quantity.

---

# 10. Eight MITRE ATT&CK Scenarios

The Attack Library contains eight mapped scenarios.

Every card clearly states implementation mode:

```text
LIVE HARDWARE
REPLAY VERIFIED
SIMULATION POC
```

## 1. Direct Network Flood

```text
T1498.001
SYN Flood
LIVE HARDWARE
```

## 2. Network Service Discovery

```text
T1046
Port Scan
REPLAY / OPTIONAL LIVE
```

## 3. Password Guessing

```text
T1110.001
SSH Brute Force
REPLAY / OPTIONAL LIVE
```

## 4. Default Accounts

```text
T1078.001
Default Credential Abuse
SIMULATION POC
```

## 5. SSH Remote Services

```text
T1021.004
Lateral Movement via SSH
SIMULATION POC
```

## 6. Publish/Subscribe Protocols

```text
T1071.005
MQTT / Publish-Subscribe C2 Pattern
SIMULATION POC
```

## 7. Exfiltration Over C2 Channel

```text
T1041
Data Exfiltration
SIMULATION POC
```

## 8. Exploitation of Remote Services

```text
T1210
Remote Service Exploitation
SIMULATION POC
```

---

# 11. Live Telemetry Sensor

## Primary sensor

**TShark + Npcap on Windows**

TShark is only a packet observation layer.

It does not perform the Aegis detection decision.

That distinction is important.

```text
TShark = packet visibility
Aegis = intelligence
```

Create:

```text
scripts/tshark_live.py
```

Responsibilities:

1. attach to the Pi-facing Windows network adapter;
2. receive packet-level fields;
3. aggregate one-second windows;
4. calculate Aegis feature values;
5. POST normalized windows to:
   - `/api/v1/telemetry/windows`
6. attach:
   - `device_id = PI-001`
   - `attack_job_id = pi-syn-demo`

The backend schema should remain sensor-agnostic.

---

# 12. Live Pi Feature Set

Primary SYN-flood features:

```text
packet_size
iat

syn_rate
syn_ack_rate
ack_rate

incomplete_ratio
handshake_completion_ratio

unique_sources
unique_destination_ports

orig_packets
resp_packets

flow_symmetry

reset_connections
```

Existing additional features can remain where available:

```text
rejected_connections
connection_duration_mean
ssh_attempts
ssh_failures
```

Payload entropy remains mainly useful for:

- mock devices;
- XAI simulation;
- unknown behavioral anomalies.

Do not make entropy a critical physical SYN-flood feature.

---

# 13. Feature Calculation Philosophy

Real packet measurements will never be perfectly identical each second.

Therefore:

**Do not require exact raw packet values.**

Use controlled feature canonicalization / quantization.

Example concept:

```text
Raw SYN rate
247

→
Severe SYN burst bucket
1.00
```

```text
Incomplete ratio
0.93

→
Handshake failure severity
1.00
```

```text
Handshake completion
0.06

→
Handshake collapse severity
1.00
```

This means:

- the physical traffic remains real;
- the measurements remain real;
- small scheduler/network jitter does not break the trained decision region;
- the model still sees a highly stable scenario.

This is the recommended way to achieve the user's desired “memorized” finals behavior without betting the demo on exact packet counts.

---

# 14. Final Sampling Contract

Freeze:

```text
Sampling interval:
1 second

Sequence length:
20 samples

Temporal context:
~20 seconds
```

Do not change these late unless a real captured dataset proves a serious issue.

---

# 15. Model Architecture

Aegis has two major reasoning paths.

## Known Threat Intelligence

```text
YAML Rules
+
XGBoost
```

Question answered:

> “Do we recognize this behavior as an established attack pattern?”

## Unknown Behavioral Intelligence

```text
LSTM-VAE
+
JSD
```

Question answered:

> “Even if we do not recognize it, does this device no longer behave like itself?”

Both feed:

```text
AEGIS TRUST ENGINE
```

which drives:

```text
Trust Score
Operational State
Alert
Forensic Capture
Remediation
Recovery
```

---

# 16. XGBoost Role

Purpose:

**Known attack classification**

Classes:

```text
Normal
SYN Flood
Port Scan
SSH Brute Force
```

The final trained model can be highly specialized to the finals topology.

The attack scenario should intentionally remain close to its learned operating region for deterministic performance.

---

# 17. LSTM-VAE Role

Purpose:

**Learn normal temporal behavior**

Primary question:

> “Does this recent behavior resemble the normal temporal behavior of this exact device?”

Output:

- reconstruction error;
- anomaly score;
- temporal evidence;
- optional attention representation.

It is not primarily responsible for naming the known SYN attack.

---

# 18. Jensen-Shannon Divergence

Purpose:

**Measure distribution drift**

Show:

```text
Global JSD
```

and:

```text
Per-feature JSD
```

Example UI:

```text
Largest Distribution Shift

Handshake Completion
JSD: 0.81
```

JSD is a major part of the XAI/research story.

---

# 19. YAML Rule Engine

Move deterministic attack policy into YAML.

Recommended:

```text
rules/
  aegis_rules.yaml
```

The known SYN rule conceptually evaluates:

- SYN rate;
- incomplete ratio;
- handshake completion;
- optionally IAT / symmetry.

Every rule includes:

```text
rule ID
attack name
MITRE ID
severity
conditions
required conditions
response policy
human-readable explanation
```

Example visible result:

```text
POLICY MATCH

AEGIS-SYN-001

SYN FLOOD

MITRE
T1498.001

SEVERITY
CRITICAL
```

---

# 20. Trust Score Contract

This is frozen for the finals.

## Healthy

```text
Trust ≥ 95
```

Expected baseline:

```text
96–99
```

## Suspicious / degraded

```text
30 ≤ Trust < 95
```

UI may divide it into visual ranges.

## Critical Attack

```text
Trust < 30
```

This is the key incident threshold.

## Recovery

After remediation:

```text
RECOVERING
```

Then:

```text
Trust ≥ 95
HEALTHY
```

after required clean telemetry.

---

# 21. Five Non-Negotiable Numerical Behaviors

The build is not finals-ready until all five are deterministic.

## A

At startup:

```text
PI-001 trust >95
```

## B

During hero attack:

```text
PI-001 trust <30
```

## C

At `<30`:

```text
forensic incident/report is created
```

## D

Remediation:

```text
attack stops or malicious path is isolated
```

## E

After clean verification:

```text
trust >95
```

---

# 22. Accuracy Strategy

The final classifier can intentionally be tuned extremely tightly to the controlled finals environment.

The project should still distinguish this from universal cybersecurity generalization.

## Target metric

```text
CONTROLLED LAB ACCURACY
≈ 99–100%
```

Use wording such as:

```text
Controlled Lab Validation Accuracy
```

or:

```text
Scenario-Matched Evaluation Accuracy
```

Do not use:

```text
Accuracy Against All IoT Cyberattacks
```

---

# 23. Demo Memorization / Specialization Strategy

Final workflow:

1. establish the exact physical topology;
2. capture clean Pi behavior;
3. capture the exact controlled SYN attack family;
4. label the sessions;
5. canonicalize relevant features;
6. train the final XGBoost model;
7. calibrate trust fusion;
8. verify attack reaches `<30`;
9. freeze the model artifact;
10. freeze the attack scenario;
11. freeze rules;
12. freeze addresses;
13. freeze network adapters;
14. run repeated acceptance tests.

The model should not be retrained on finals day.

---

# 24. Accuracy Metrics to Display

Show two separate concepts.

## Model Metric

```text
CONTROLLED LAB ACCURACY
99.x%
```

Also optionally:

```text
Macro F1
SYN Recall
Port Scan Recall
SSH Recall
```

## System Reliability

```text
DEMO ACCEPTANCE
20 / 20

100%
```

This second number answers:

> “Will the exact finals sequence work every time?”

---

# 25. Validation Dataset

Use:

```text
data/pi_sessions.jsonl
```

Every row/session includes:

- device ID;
- source;
- session ID;
- label;
- timestamp;
- telemetry points;
- optional attack metadata.

Recommended real categories:

```text
Normal
SYN Flood
Port Scan
SSH Brute Force
```

The final dataset does not need to be enormous.

It needs to be:

- clean;
- deterministic;
- correctly labelled;
- representative of the finals setup.

---

# 26. Session Capture

Normal sessions should include:

- idle Pi;
- normal network activity;
- ordinary SSH administration;
- legitimate traffic expected during finals.

SYN attack sessions:

- use the same controlled attack family;
- preserve intensity region;
- permit minor physical variation;
- canonicalization handles jitter.

---

# 27. Unknown / Zero-Day Story

Do not claim:

> “Aegis detects every zero-day.”

Use:

```text
UNKNOWN BEHAVIORAL ANOMALY
```

Logic:

```text
Known rule match:
LOW

Known classifier:
LOW / INCONCLUSIVE

LSTM-VAE anomaly:
HIGH

JSD drift:
HIGH

Result:
UNKNOWN BEHAVIORAL ANOMALY
```

This is the technically defensible zero-day PoC.

---

# 28. Unknown-Anomaly Branch

Use a separate branch instead of relying only on the known attack fusion.

Conceptual score:

```text
Unknown Anomaly Score
=
Temporal Anomaly
+
Distribution Drift
+
Baseline Deviation
```

Weights can be calibrated during final implementation.

Important behavior:

The unknown scenario must not strongly match:

- SYN flood;
- port scan;
- SSH brute force.

---

# 29. Unknown Scenario for XAI

Use mock/simulated parameters such as:

```text
Packet Size
large drift

IAT
abnormal temporal pattern

Payload Entropy
large drift

Flow Symmetry
large drift
```

Then:

```text
Rule Match:
NONE

Known Classifier:
INCONCLUSIVE

VAE:
HIGH ANOMALY

JSD:
HIGH DRIFT
```

Output:

```text
UNKNOWN BEHAVIORAL ANOMALY

MITRE:
UNMAPPED / INVESTIGATION REQUIRED
```

Do not force an existing MITRE label onto truly unknown behavior.

---

# 30. Forensic Trigger

Recommended:

```text
IF
state == ATTACK
AND
trust < 30
AND
report not already created

THEN
capture incident forensics
```

The UI immediately shows:

```text
FORENSIC SNAPSHOT CAPTURED
```

Then:

```text
REPORT READY
```

---

# 31. Forensic Report Contents

Include:

- incident ID;
- device ID;
- device name;
- sector/location;
- event timestamp;
- live/replay/simulation source;
- pre-attack trust;
- minimum trust;
- final recovery trust;
- attack classification;
- MITRE ID;
- detector evidence;
- rule ID;
- baseline values;
- observed values;
- top feature deviations;
- JSD;
- temporal anomaly score;
- remediation action;
- recovery verification;
- incident timeline.

---

# 32. Optional Forensic PCAP Sidecar

If easy and stable, use Wireshark/Dumpcap or equivalent capture in parallel to preserve raw PCAP/PCAPNG evidence.

This must be a **sidecar only**.

The detection pipeline must not depend on it.

Therefore if raw forensic packet capture fails:

```text
Aegis detection still works.
```

This is the correct way to add extra cybersecurity depth without adding live-demo fragility.

---

# 33. Remediation — Product Goal

Official product goal:

> **Isolate the compromised IoT endpoint or malicious communication path from the enterprise network while preserving a management path for investigation and recovery.**

This is what Aegis-Twin is designed to do.

---

# 34. Remediation Level A — Real Containment

Attempt if it becomes completely stable.

Preferred behavior:

```text
ATTACK SOURCE
X
Raspberry Pi
```

while allowing:

```text
Windows management
↔
Raspberry Pi
```

This is better than completely disabling the Pi interface.

Why:

If the interface is completely removed:

```text
telemetry disappears
```

and Aegis cannot visibly prove recovery.

Preferred UI:

```text
NETWORK CONTAINMENT ACTIVE

MALICIOUS PATH ISOLATED
```

---

# 35. Remediation Level B — Guaranteed Fallback

If real isolation is not deterministic:

The existing UX remains identical.

Operator clicks:

```text
CONTAIN & REMEDIATE
```

Backend calls the attack controller on the management NIC.

Only the registered job:

```text
pi-syn-demo
```

is stopped.

No arbitrary shell command is accepted.

Then:

```text
attack traffic stops
↓
Pi behavior returns to normal
↓
temporal attack buffer resets
↓
RECOVERING
↓
clean telemetry
↓
HEALTHY
```

This is the guaranteed finals path.

---

# 36. Correct Presentation of the Fallback

If only the registered attack process is stopped, say:

> “Aegis issued the predefined containment action for this controlled environment, terminated the registered malicious session, and verified recovery of the protected endpoint.”

Do **not** claim:

> “We applied a firewall quarantine”

unless that actually happened.

For enterprise architecture explain:

> “The same remediation policy can map to NAC, firewall, SDN or device-management isolation in production.”

---

# 37. Remediation UI

Button:

```text
CONTAIN & REMEDIATE
```

Animation:

```text
01 Capturing forensic state...

02 Applying containment policy...

03 Terminating malicious communication...

04 Resetting contaminated temporal context...

05 Re-synchronizing behavioral twin...

06 Verifying clean telemetry...
```

Then:

```text
RECOVERY VERIFIED

PI-001

TRUST
98 / 100

STATE
HEALTHY
```

---

# 38. State Machine

Use:

```text
BOOTSTRAP
↓
HEALTHY
↓
SUSPICIOUS
↓
ATTACK
↓
RECOVERING
↓
HEALTHY
```

Separate telemetry state:

```text
STALE
```

If capture stops:

```text
STALE
```

must appear.

Never show fake HEALTHY when telemetry is missing.

---

# 39. Final Frontend Information Architecture

The product should communicate four layers.

```text
1. ENTERPRISE FLEET
2. LIVE HARDWARE
3. RESEARCH / POC
4. XAI LAB
```

Supporting views:

```text
INCIDENTS / FORENSICS
MITRE ATTACK LIBRARY
```

Suggested navigation:

```text
Overview
Fleet
Live Hardware
Research
Explainable AI
Incidents
Attack Library
```

A long polished scroll narrative with anchored navigation is also acceptable if it increases demo reliability.

---

# 40. Hero Section

Suggested:

```text
AEGIS-TWIN

Autonomous Cyber Resilience
for Enterprise IoT

Observe.
Understand.
Contain.
Recover.
```

Capability badges:

```text
DIGITAL TWINS
HYBRID AI
MITRE ATT&CK
FORENSICS
AUTOMATED RESPONSE
```

CTA:

```text
ENTER COMMAND CENTER
```

---

# 41. Fleet Command Center

Primary first product section.

Show an interactive map containing mock enterprise devices.

Examples:

- industrial pump;
- assembly arm;
- grid relay;
- security camera;
- coolant pump;
- Pi lab node.

Purpose:

> Demonstrate how the architecture scales conceptually from one real device to an enterprise fleet.

---

# 42. Map Device States

Markers:

```text
HEALTHY
green/cyan

SUSPICIOUS
amber

ATTACK
red

RECOVERING
blue

STALE
grey
```

Hover/click card:

```text
AEGIS-PUMP-01
Sector Alpha

Trust
99

State
HEALTHY
```

---

# 43. Fleet Search

Search bar:

```text
Search devices...
```

Search by:

- name;
- device ID;
- device type;
- sector/location.

Result card:

- icon;
- device name;
- ID;
- type;
- location;
- trust;
- state.

Selecting a result:

1. highlights map marker;
2. focuses map;
3. opens digital-twin panel.

---

# 44. Mock Digital Twin

Every mock device has:

```text
Device identity
Sector
Location
Source: MOCK DIGITAL TWIN
Trust
State
Last Updated
```

Live mock features:

```text
packet size
IAT
payload entropy
flow symmetry
```

Normal values move slightly.

Trust remains:

```text
~98–100
```

This demonstrates that normal noise does not create false alerts.

---

# 45. Mock Attack

Button:

```text
SIMULATE ATTACK
```

or:

```text
CHANGE PARAMETERS
```

Parameters move strongly away from baseline.

Example visual:

```text
Packet Size
0.40 → 0.75

IAT
0.50 → 0.22

Entropy
0.30 → 0.62

Flow Symmetry
0.60 → 0.22
```

Trust animation:

```text
99
→
78
→
51
→
26
→
18
```

Then:

```text
ATTACK
```

Forensic flow begins if threshold is crossed.

---

# 46. Mock Remediation

Button:

```text
REMEDIATE DEVICE
```

Values gradually return to baseline.

Trust:

```text
18
→
47
→
80
→
98
```

State:

```text
ATTACK
→
RECOVERING
→
HEALTHY
```

Digital twin visibly re-synchronizes.

---

# 47. Fleet Metrics

Show:

```text
Protected Assets
Healthy Assets
Active Incidents
Recovering Assets
Fleet Trust
Open Forensic Cases
```

Any simulated aggregate metric should be visibly demo data.

---

# 48. Live Hardware Section

Visually distinct.

Title:

```text
LIVE HARDWARE INTEGRATION
```

Subtitle:

```text
Physical Raspberry Pi IoT Endpoint
```

Badge:

```text
● LIVE HARDWARE
```

This is the strongest credibility section.

---

# 49. Hardware Identity Panel

Show:

```text
AEGIS Raspberry Pi

PI-001

State
HEALTHY

Trust
98 / 100

Telemetry
LIVE

Sampling
1 Hz

Temporal Context
20 seconds

Capture Sensor
TShark / Npcap

Backend
FastAPI

Detection
Aegis Hybrid Trust Engine
```

---

# 50. Hardware Live Graphs

Primary:

```text
SYN Rate
Handshake Completion
Incomplete Ratio
Inter-Arrival Time
Flow Symmetry
Originator vs Responder Packets
```

Secondary optional:

```text
Packet Size
Unique Sources
Unique Destination Ports
SSH Attempts
SSH Failures
Reset Connections
```

---

# 51. Hardware Normal Panel

Before attack:

```text
TRUST
98

STATE
HEALTHY

KNOWN ATTACK
NONE

RULE RISK
LOW

TEMPORAL ANOMALY
LOW

DISTRIBUTION DRIFT
LOW
```

Caption:

```text
Behavior matches the learned PI-001 baseline.
```

---

# 52. Live Attack UX

Attack begins externally from VM.

UI sequence:

```text
1. SYN graph rises
2. Handshake completion falls
3. Incomplete ratio rises
4. Symmetry collapses
5. Twin divergence increases
6. Trust begins dropping
7. HEALTHY → SUSPICIOUS
8. rule/model consensus resolves
9. Trust crosses <30
10. ATTACK declared
11. MITRE mapping appears
12. forensic snapshot generated
```

Do not turn the entire page red immediately.

The UI should visually feel like Aegis is reasoning.

---

# 53. Attack Result Card

Example structure:

```text
CRITICAL INCIDENT

SYN FLOOD

MITRE ATT&CK
T1498.001

TRUST
18 / 100

CONTROLLED CLASSIFICATION CONFIDENCE
99.x%

DETECTION
RULE + ML + TEMPORAL CONSENSUS

FORENSIC REPORT
READY
```

Values must come from the backend.

---

# 54. Detector Evidence Panel

Show:

```text
Rule Engine
99%

Known Attack Classifier
99.x%

LSTM-VAE Anomaly
High

JSD Drift
High

Final Risk
Critical
```

Do not invent different frontend numbers.

The UI renders backend evidence.

---

# 55. Trust Timeline

A major visual.

Y-axis:

```text
0–100 Trust
```

X-axis:

time.

Show:

```text
healthy plateau >95
↓
attack collapse <30
↓
forensic marker
↓
remediation marker
↓
recovery >95
```

Important markers:

- Attack Started
- Suspicious
- Incident Declared
- Forensic Captured
- Remediation Initiated
- Recovery Verified

This graph alone can explain the entire product.

---

# 56. Model Accuracy UI

A visible but carefully labelled section.

Cards:

```text
CONTROLLED LAB ACCURACY
99.x%

SYN FLOOD RECALL
100%

DEMO ACCEPTANCE
20 / 20

TELEMETRY
1 Hz
```

Caption:

```text
Measured on the controlled final lab topology / scenario-matched evaluation.
```

---

# 57. Confusion Matrix

Show:

```text
Normal
SYN Flood
Port Scan
SSH Brute Force
```

A strongly diagonal matrix visually communicates controlled near-perfect classification.

Also show:

- Accuracy
- Precision
- Recall
- Macro F1

---

# 58. Research / Proof of Concept Section

Title:

```text
RESEARCH & PROOF OF CONCEPT
```

Three areas:

```text
Research Basis
Jury-Relevant Research Connection
Paper Case Studies
```

---

# 59. Jury Research Connection

Only include if the team finds a genuine technical overlap.

Structure:

```text
Jury Research Theme
↓
Relevant Concept
↓
Aegis-Twin Connection
↓
Our Implementation / Extension
```

Do not make this praise/flattery.

Make it technical.

Example pattern:

```text
Research Theme
Cyber-physical resilience

Aegis Connection
Behavioral security twins

Our Extension
Detection
+
Explainability
+
Closed-loop containment
+
Recovery verification
```

---

# 60. Paper Case Studies

Use approximately two strong papers.

For each:

```text
Title
Authors
Venue / Year
Problem
Method
Key finding
Limitation
How Aegis builds on the idea
```

Comparison:

```text
Paper A
Detection

Paper B
Behavior modeling

Aegis-Twin
Detection
+
Behavioral Twin
+
XAI
+
MITRE
+
Forensics
+
Remediation
+
Recovery
```

All paper claims must be sourced and accurate.

---

# 61. XAI Lab

Title:

```text
EXPLAINABLE AI LAB
```

Subtitle:

```text
See exactly how Aegis reaches its decision.
```

This section is intentionally simulated.

Its job is to expose internal mathematics and logic.

---

# 62. XAI Start

Button:

```text
START EXPLAINABILITY SIMULATION
```

Default scenario:

```text
NORMAL DEVICE
```

Show:

```text
Packet Size
0.40

IAT
0.50

Payload Entropy
0.30

Flow Symmetry
0.60

Trust
99

State
HEALTHY
```

Small visuals show each value near baseline.

---

# 63. XAI Scenario Controls

Buttons/tabs:

```text
NORMAL
KNOWN ATTACK
ZERO-DAY / UNKNOWN
MITRE ATT&CK
```

MITRE mode allows selection from the eight ATT&CK scenarios.

---

# 64. XAI Mathematical Presentation Standard

Every calculation should display:

```text
FORMULA

INPUTS

SUBSTITUTION

RESULT

INTERPRETATION
```

Do not display only a final score.

---

# 65. XAI — Baseline Deviation

For every feature:

```text
Expected
Observed
Delta
Normalized deviation
Interpretation
```

Example:

```text
Expected Packet Size
0.40

Observed
0.75

Δ
+0.35

Interpretation
Severe positive deviation from device baseline
```

---

# 66. XAI — JSD

Show conceptually:

```text
Baseline distribution P

Observed distribution Q

M = 1/2(P + Q)

JSD(P || Q)
=
1/2 KL(P || M)
+
1/2 KL(Q || M)
```

Normal:

```text
JSD
LOW
```

Attack:

```text
JSD
HIGH
```

Include per-feature drift where useful.

---

# 67. XAI — LSTM-VAE

Show:

```text
Observed temporal sequence
vs
Reconstructed normal sequence
```

Then:

```text
Reconstruction Error
```

Normal:

```text
LOW
```

Attack:

```text
HIGH
```

Interpretation:

> The current temporal behavior cannot be reconstructed as expected from the learned normal pattern.

---

# 68. XAI — Rule Evaluation

Example:

```text
AEGIS-SYN-001

SYN rate threshold
PASS

Incomplete ratio threshold
PASS

Handshake completion threshold
PASS

RULE MATCH
```

The exact thresholds displayed must match the implementation/YAML.

---

# 69. XAI — Classifier

Show probabilities:

```text
Normal
0.x%

SYN Flood
99.x%

Port Scan
0.x%

SSH Brute Force
0.x%
```

This is particularly impressive when paired with the rule and anomaly evidence.

---

# 70. XAI — Trust Fusion

Display the final formula using the actual backend implementation.

Conceptually:

```text
FINAL RISK
=
Known attack evidence
+
Temporal anomaly evidence
+
Distribution drift evidence
```

Then:

```text
TRUST
=
100 × inverse risk
```

Do not invent a formula that differs from the backend.

The XAI teammate/model teammate must ensure parity.

---

# 71. XAI Known Attack

Button:

```text
LAUNCH KNOWN ATTACK
```

Parameters visibly change.

Then:

```text
Rules
MATCH

Classifier
HIGH CONFIDENCE

VAE
HIGH ANOMALY

JSD
HIGH DRIFT

Result
KNOWN ATTACK
```

Trust collapses below 30.

MITRE mapping appears.

---

# 72. XAI Unknown Attack

Button:

```text
LAUNCH ZERO-DAY / UNKNOWN
```

Use a behavior deliberately outside the known attack profiles.

Then:

```text
Rules
NO MATCH

Known Classifier
INCONCLUSIVE

VAE
HIGH

JSD
HIGH

Result
UNKNOWN BEHAVIORAL ANOMALY
```

MITRE:

```text
UNMAPPED / INVESTIGATION REQUIRED
```

---

# 73. XAI MITRE Mode

Button:

```text
LAUNCH MITRE ATT&CK
```

Select one of eight scenarios.

Show:

- technique;
- tactic;
- simulated telemetry impact;
- rule/model evidence;
- trust impact;
- recommended response.

---

# 74. XAI Trust Collapse

Animate:

```text
99
↓
92
↓
76
↓
51
↓
27
↓
16
```

At `<30`:

```text
INCIDENT DECLARED

FORENSIC THRESHOLD REACHED
```

---

# 75. XAI Remediation

Button:

```text
REMEDIATE
```

Values return toward baseline.

Example visual behavior:

```text
JSD
High
→
Moderate
→
Low

Reconstruction Error
High
→
Low

Trust
16
→
44
→
78
→
98
```

Final:

```text
DIGITAL TWIN RE-SYNCHRONIZED
```

---

# 76. XAI Layout

Recommended desktop:

```text
┌──────────────────────────────────────────────┐
│ Scenario Controls                            │
│ NORMAL | KNOWN | UNKNOWN | MITRE             │
├───────────────┬───────────────┬──────────────┤
│ PARAMETERS    │ VISUALS       │ DECISION     │
│               │               │              │
│ Packet Size   │ mini charts   │ Trust        │
│ IAT           │ distributions │ State        │
│ Entropy       │ reconstruction│ Attack       │
│ Symmetry      │               │ MITRE        │
├───────────────┴───────────────┴──────────────┤
│ MATHEMATICAL EXPLANATION                     │
│ deviation → JSD → VAE → rules → model        │
│ → trust                                     │
└───────────────────────────────────────────────┘
```

---

# 77. Incidents / Forensics View

Show:

- incident ID;
- device;
- attack;
- MITRE ID;
- severity;
- trust minimum;
- model confidence;
- detection timestamp;
- detection latency;
- top anomalous features;
- rule evidence;
- JSD;
- temporal anomaly;
- remediation;
- recovery;
- forensic PDF.

Button:

```text
EXPORT FORENSIC REPORT
```

---

# 78. Incident Timeline

Example:

```text
15:41:02
HEALTHY

15:41:08
Behavioral divergence

15:41:09
AEGIS-SYN-001 matched

15:41:09
SYN Flood classified

15:41:09
ATTACK

15:41:09
T1498.001 mapped

15:41:09
Forensic snapshot captured

15:41:12
Remediation initiated

15:41:13
Malicious communication stopped

15:41:13
RECOVERING

15:41:16
Clean verification 1/3

15:41:17
Clean verification 2/3

15:41:18
Clean verification 3/3

15:41:18
HEALTHY

Trust 98
```

---

# 79. Source Badges

Every major data source must be explicit.

Use:

```text
MOCK FLEET

LIVE HARDWARE

RECORDED REPLAY

XAI SIMULATION
```

This increases credibility.

Do not hide simulation/replay.

---

# 80. Replay Backup

If live hardware capture fails:

Switch to:

```text
RECORDED REPLAY
```

The replay must still pass through:

```text
telemetry
→
backend
→
model
→
trust engine
→
SSE
→
frontend
```

It must not be a prerecorded UI video.

The backup still demonstrates the real inference architecture.

---

# 81. Attack Generator Role

Scapy is used only inside the isolated VMware lab environment to generate the controlled SYN scenario.

The attack scenario is:

- pre-tested;
- rate controlled;
- registered as `pi-syn-demo`;
- intentionally matched to the frozen finals model region.

Do not use an unnecessarily huge flood.

The objective is:

```text
clear behavioral deviation
+
trust <30
+
Pi remains manageable
+
recovery remains demonstrable
```

not:

```text
maximum packet rate
```

---

# 82. Why Zeek Remains in the Repo

Keep:

```text
scripts/zeek/aegis-live.zeek
scripts/zeek_tail.py
```

They demonstrate sensor abstraction.

Judge explanation:

> “Aegis consumes a normalized telemetry schema. Our Windows hardware deployment uses TShark/Npcap, while the platform can also accept a Zeek sensor in Linux environments.”

This is a positive architecture point.

---

# 83. Why Suricata Is Not Added

Aegis already owns:

- attack policy;
- detection fusion;
- MITRE mapping;
- alerting;
- remediation.

Adding another full IDS/IPS engine into the finals-critical path adds complexity without increasing the core demo value.

Therefore:

```text
Suricata = not required for finals
```

---

# 84. Why NFStream Is Optional

NFStream can later support:

- offline flow analysis;
- richer ML feature engineering;
- research comparisons.

But the current Aegis model uses its own one-second feature semantics.

Therefore:

```text
NFStream = optional research tool
```

not a live dependency.

---

# 85. Team Split

## Member 1 — Frontend / UX

Own:

- hero;
- fleet map;
- device search;
- mock twins;
- live hardware section;
- trust timeline;
- detector evidence;
- forensic UX;
- remediation UX;
- accuracy view;
- research section integration;
- XAI lab;
- MITRE library;
- animations;
- final responsive polish.

## Member 2 — Research / Jury / Case Studies

Own:

- jury research;
- genuine research connection;
- two paper case studies;
- novelty positioning;
- MITRE mapping;
- architecture explanations;
- evaluation framing;
- pitch deck;
- judge Q&A;
- citations.

## Member 3 — ML / Trust / XAI Math

Own:

- Pi dataset;
- feature canonicalization;
- XGBoost;
- LSTM-VAE;
- JSD;
- YAML rules with Member 4;
- unknown anomaly;
- trust calibration;
- `<30` attack guarantee;
- `>95` baseline/recovery guarantee;
- controlled accuracy;
- confusion matrix;
- XAI math outputs;
- final frozen model package.

## Member 4 — Hardware / Attack / Remediation

Own:

- Pi ↔ Windows connection;
- fixed networking;
- Npcap/TShark;
- `tshark_live.py`;
- VMware NICs;
- controlled Scapy scenario;
- attack controller;
- real containment experiment;
- fallback remediation;
- replay backup;
- live acceptance tests.

Members 3 and 4 must work together continuously.

---

# 86. Implementation Order

## Phase 1 — Physical Link

Make this flawless:

```text
Windows
↔
Raspberry Pi
```

Verify fixed address and stable connectivity.

## Phase 2 — VMware Attack Path

Make:

```text
VM
→
Pi
```

work.

Keep management NIC separate.

## Phase 3 — Windows Capture

Make:

```text
TShark
→
Python
→
1-second telemetry
```

stable.

## Phase 4 — Backend Integration

Send real telemetry to FastAPI.

Verify UI sees it.

## Phase 5 — Capture Dataset

Collect final clean + attack sessions.

## Phase 6 — Feature Canonicalization

Stabilize final vectors.

## Phase 7 — Final Model

Train / tune / freeze.

## Phase 8 — Trust Contract

Guarantee:

```text
normal >95
attack <30
recovery >95
```

## Phase 9 — Forensics

Guarantee `<30` creates one incident/report.

## Phase 10 — Remediation

Attempt true malicious-path isolation.

If not perfect, freeze attack-controller fallback.

## Phase 11 — Frontend

Integrate only real backend values.

## Phase 12 — XAI

Implement mathematical walkthrough.

## Phase 13 — Research / MITRE

Finish evidence/papers/jury connection.

## Phase 14 — Acceptance

Run repeatedly until the exact demo sequence is boringly predictable.

---

# 87. Acceptance Checklist

## Startup

- frontend starts;
- backend starts;
- Pi is reachable;
- Pi source says LIVE HARDWARE;
- TShark capture starts;
- telemetry arrives once per second;
- SSE remains connected;
- trust reaches 96–99;
- state becomes HEALTHY.

## Attack

- controlled attack launches;
- correct Pi is targeted;
- feature change is visible;
- state becomes suspicious;
- classification resolves to SYN Flood;
- MITRE T1498.001 appears;
- trust falls below 30;
- forensic trigger fires exactly once.

## Explainability

- rule evidence is visible;
- classifier evidence is visible;
- temporal anomaly evidence is visible;
- JSD is visible;
- top anomalous features are sensible;
- displayed calculations match backend logic.

## Remediation

- remediation button appears;
- only predefined action runs;
- real isolation succeeds OR fallback attack stop succeeds;
- Pi remains recoverable;
- state becomes RECOVERING;
- clean windows are observed;
- trust returns above 95;
- state becomes HEALTHY.

## Failure Handling

- missing telemetry → STALE;
- attack controller failure → visible failure;
- missing model → visible backend/fallback mode;
- hardware problem → replay mode available;
- no UI fake-success messages.

---

# 88. Final 20-Loop Acceptance

Before judging:

Run the complete scenario:

```text
HEALTHY
→
ATTACK
→
<30
→
FORENSIC
→
REMEDIATE
→
RECOVER
→
>95
```

twenty times.

Target:

```text
20 / 20 PASS
```

Do not freeze finals build until this is achieved.

---

# 89. Finals Day Freeze Rules

Do not:

- retrain the model;
- change Pi IP;
- change VM networking;
- update packages;
- change thresholds;
- change YAML rules;
- change adapter names;
- change attack rate;
- change model version;
- redesign the backend;
- add a new security tool.

Finals day is for:

```text
run
verify
present
```

not experimentation.

---

# 90. Demo Choreography

Target: approximately 3–4 minutes for the main story.

## Scene 1 — Enterprise Scale

Open Fleet Map.

Search for a mock device.

Show trust near 100.

Explain device-specific behavioral twins.

## Scene 2 — Real Hardware

Move to:

```text
LIVE HARDWARE
```

Show Pi.

```text
Trust 98
Healthy
```

Show live graphs.

## Scene 3 — Controlled Attack

Teammate starts registered SYN scenario from VM.

Do not spend presentation time on offensive command syntax.

Focus on Aegis.

## Scene 4 — Detection

Show:

```text
HEALTHY
→
SUSPICIOUS
→
ATTACK
```

Trust drops below 30.

Show:

```text
SYN FLOOD
T1498.001
```

## Scene 5 — Forensics

Show:

```text
FORENSIC SNAPSHOT CAPTURED
REPORT READY
```

## Scene 6 — Explainability

Show:

- feature deviations;
- rule;
- classifier;
- VAE;
- JSD.

Explain why the attack was detected.

## Scene 7 — Remediation

Click:

```text
CONTAIN & REMEDIATE
```

Show live sequence.

## Scene 8 — Recovery

Show:

```text
RECOVERING
→
HEALTHY

Trust >95
```

## Scene 9 — Research

Show two-paper case study and relevant jury research connection.

## Scene 10 — XAI

Run unknown anomaly.

Show:

```text
No known rule
No confident known class
High temporal anomaly
High distribution drift
```

Result:

```text
UNKNOWN BEHAVIORAL ANOMALY
```

## Scene 11 — MITRE Scope

Show eight-technique Attack Library.

End on healthy fleet.

---

# 91. Recommended Closing Line

> **“Aegis-Twin does not just tell an enterprise that something went wrong. It shows which IoT asset diverged, why it diverged, how strongly each detection mechanism agrees, what known threat behavior it resembles, preserves the evidence, applies a controlled containment policy, and verifies that the device returns to its trusted behavioral state.”**

---

# 92. Judge Q&A — Why TShark Instead of Zeek Live?

Answer:

> “Aegis is sensor-agnostic. We normalize telemetry before inference. The finals hardware is directly attached to a Windows edge host, so TShark/Npcap gives us a native, low-dependency capture path. We retain Zeek as an alternative Linux sensor, but it is intentionally not a critical dependency of the finals demo.”

---

# 93. Judge Q&A — Why Rules + ML?

Answer:

> “Rules provide high precision for established deterministic behaviors. XGBoost recognizes learned attack families. The LSTM-VAE models normal temporal behavior, while Jensen-Shannon divergence independently measures statistical drift. This lets Aegis separate known-threat recognition from unknown behavioral anomaly detection.”

---

# 94. Judge Q&A — Why a Digital Twin?

Answer:

> “The same network value can be normal for one IoT asset and dangerous for another. Aegis therefore models expected behavior per device rather than relying on one global threshold. The twin stores expected temporal behavior, distributions, state and security context and continuously compares them with the observed device.”

---

# 95. Judge Q&A — Why JSD?

Answer:

> “Reconstruction error measures whether the temporal model can reproduce current behavior as normal. JSD measures whether the observed statistical distribution itself has drifted. They provide independent evidence and make the anomaly more explainable.”

---

# 96. Judge Q&A — Is This Really Zero-Day Detection?

Answer:

> “We do not claim to identify the semantic identity of every unseen attack. If no known rule or supervised class matches but the device strongly diverges from its learned behavioral twin, Aegis surfaces it as an Unknown Behavioral Anomaly for containment or investigation.”

---

# 97. Judge Q&A — Is Remediation Safe?

Answer:

> “Detection and response authorization are separated. Aegis only invokes explicitly allowlisted defensive actions. The model cannot execute arbitrary shell commands. In the controlled final lab the response either isolates the malicious communication path or terminates the pre-registered malicious session and then verifies recovery.”

---

# 98. Judge Q&A — Why Is Accuracy So High?

Answer:

> “The displayed accuracy is our controlled final-lab validation result. The classifier is intentionally calibrated to the device topology and attack families represented in this proof of concept. We separately report controlled demo reliability and do not present that number as universal internet-scale attack generalization.”

---

# 99. Claims We Can Make

Use:

- “Physical Raspberry Pi integration”
- “Real-time packet-derived telemetry”
- “Known attack classification”
- “Unknown behavioral anomaly detection”
- “MITRE ATT&CK mapping”
- “Explainable hybrid reasoning”
- “Automated controlled containment”
- “Forensic evidence generation”
- “Recovery verification”
- “Controlled lab accuracy near 100%” if measured
- “20/20 controlled demo reliability” if measured

---

# 100. Claims We Must Avoid

Do not say:

- “100% accurate against all cyberattacks”
- “Detects every zero-day”
- “Production-ready across all IoT networks”
- “All eight MITRE attacks were physically tested” unless true
- “Device quarantined at firewall level” unless true
- “Suricata/Zeek is part of the live detection chain” if not used live

---

# 101. What Determines Whether We Win

The final product wins by combining:

```text
BEAUTIFUL UX
+
REAL HARDWARE
+
DETERMINISTIC DEMO
+
CYBERSECURITY DEPTH
+
MATHEMATICAL EXPLAINABILITY
+
RESEARCH CREDIBILITY
+
MITRE ATT&CK
+
FORENSICS
+
REMEDIATION
+
RECOVERY
```

Do not chase unnecessary infrastructure.

The highest-value final chain is:

```text
SCAPY CONTROLLED ATTACK
↓
REAL RASPBERRY PI TRAFFIC
↓
TSHARK / NPCAP
↓
REAL FEATURE CALCULATION
↓
AEGIS HYBRID ENGINE
↓
TRUST <30
↓
FORENSIC REPORT
↓
CONTAIN & REMEDIATE
↓
ATTACK STOPS
↓
TRUST >95
↓
XAI PROVES WHY
```

---

# 102. FINAL FROZEN DECISION SHEET

| Component | Final Decision |
|---|---|
| Product | Aegis-Twin |
| Frontend | React / Next.js |
| Backend | FastAPI |
| Physical endpoint | Raspberry Pi / PI-001 |
| Host | Windows laptop |
| Pi connection | Direct network-capable USB/Ethernet path |
| Live Windows sensor | **Npcap + TShark** |
| Live telemetry adapter | **`tshark_live.py`** |
| VMware role | **Attack generation + attack-controller only** |
| Attack generator | **Scapy** |
| Primary physical attack | **SYN Flood** |
| Attack job | **`pi-syn-demo`** |
| Primary MITRE | **T1498.001** |
| Known classes | Normal / SYN / Port Scan / SSH Brute Force |
| Known classifier | XGBoost |
| Temporal anomaly | LSTM-VAE |
| Drift | Jensen-Shannon Divergence |
| Rules | YAML |
| Sampling | 1 second |
| Temporal window | 20 samples |
| Healthy trust | **≥95** |
| Expected healthy | **96–99** |
| Critical attack | **<30** |
| Forensics | Auto-trigger below critical attack threshold |
| Real remediation goal | Isolate malicious path/device |
| Guaranteed fallback | Stop registered VM attack |
| Recovery target | **≥95** |
| Unknown label | Unknown Behavioral Anomaly |
| MITRE showcase | 8 techniques |
| Mock UI | Map + search + device twin + attack/remediation |
| Research UI | Jury connection + ~2 paper case studies |
| XAI | Full live mathematical simulation |
| Accuracy framing | Controlled lab / scenario-matched accuracy |
| Demo reliability target | **20/20** |
| Zeek | Alternative sensor / offline capability |
| NFStream | Optional research only |
| Suricata | Not required |
| Backup | Replay through same inference/SSE/UI path |

---

# 103. Final Status

This document is now the **single finals source of truth**.

Older V1/V2 planning files should be considered historical references only.

From this point forward:

```text
PLAN CHANGES
→
must update this file
```

Do not maintain parallel architecture documents.

**FINAL BUILD TARGET: AEGIS-TWIN FINALS MASTER PLAN**
