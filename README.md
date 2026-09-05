Aegis-Twin

Explainable Cyber-Resilience Digital Twin for Enterprise and Industrial IoT

Detecting an attack is only the beginning. The harder question is: when can the device be trusted again?

Aegis-Twin is an explainable cyber-resilience digital twin that continuously models the expected behaviour of an IoT device, detects both known and previously unseen deviations, explains why trust was lost, preserves forensic evidence, supports controlled remediation, and verifies recovery before restoring the device to a healthy state.

The project follows one complete operational loop:

Observe -> Detect -> Explain -> Prove -> Forensics -> Remediate -> Recover

Unlike a conventional IDS that stops at an alert or attack label, Aegis-Twin treats security as a continuous device trust problem.

Why Aegis-Twin

IoT and IIoT devices are heterogeneous, resource-constrained and often long-lived. A behaviour that is normal for one endpoint may be highly abnormal for another, which makes a single global threshold or classifier insufficient.

Our design was shaped by research on behavioural intrusion detection, temporal anomaly detection, explainable AI, ensemble learning and cybersecurity digital twins. We also studied the direction of mature industry platforms such as Armis, Nozomi Networks and Darktrace. Aegis-Twin does not try to replace these platforms; its research focus is the device-level, inspectable trust and recovery lifecycle from physical observation to verified re-entry into a trusted state.

Core contribution

Aegis-Twin combines four complementary evidence sources instead of trusting a single model:

Layer

Role

YAML Security Rules

Deterministic, high-confidence evidence for known behaviours

XGBoost

Classification of known attack families

LSTM-VAE

Temporal behavioural anomaly detection for unseen or unusual behaviour

Jensen-Shannon Divergence

Distribution-drift evidence against the learned device baseline

For the Raspberry Pi profile, the Trust Composer uses the calibrated fusion:

Rule evidence       50%
XGBoost             30%
LSTM-VAE            15%
JSD                   5%

The active temporal model uses a 20-point context at 1-second sampling, with a 64-unit LSTM-VAE, 16-dimensional latent space, and learned temporal attention.

Operational trust states are intentionally interpretable:

Trust >= 95      HEALTHY
Trust < 30       confirmed ATTACK region
After response   RECOVERING until clean evidence is re-established

A device is not declared healthy immediately after an attack is stopped. Aegis-Twin requires 3 consecutive clean telemetry windows before verified recovery.

Controlled ablation study

We performed a controlled prototype ablation study to test whether the hybrid architecture contributes more than any individual detector alone.

Configuration

Accuracy

Macro F1

Unknown-behaviour capability

XGBoost only

96.1%

95.4%

Low

LSTM-VAE only

91.8%

90.7%

High

JSD only

86.9%

84.8%

Medium

Rules + XGBoost

97.4%

96.9%

Low

LSTM-VAE + JSD

94.2%

93.6%

High

Aegis full ensemble

99.1%

98.8%

High

The result supports the design choice behind Aegis-Twin: supervised classification is strong for known attacks, temporal and distributional models add coverage for unseen behaviour, and deterministic rules provide high-confidence evidence. The full ensemble produced the strongest overall result in the controlled prototype evaluation.

Evaluation scope: these percentages are controlled prototype ablation results used to compare system configurations under the same evaluation setup. They are not presented as universal production-network accuracy.

Physical validation

Aegis-Twin was not evaluated only through a simulated dashboard. The finals prototype was validated using a real Raspberry Pi endpoint and real packet-derived telemetry.

Physical dataset

Independent physical sessions : 12
Normal sessions               : 6
SYN-flood sessions            : 6
20-point windows              : 84
Normal windows                : 66
SYN-flood windows             : 18
Underlying 1-second points    : 1680

Measured separation

Feature

Normal mean

Physical SYN mean

SYN rate

0.1864

195.2917

Incomplete-connection ratio

0.0144

0.9944

Handshake completion

0.9856

0.0056

Inter-arrival time

0.8085

0.0234

Flow symmetry

0.9752

0.4972

Origin packets

0.7432

195.2917

Response packets

0.7038

97.6333

The physical data was used for finals calibration. The normal-only PI LSTM-VAE was calibrated using a held-out physical normal session, while XGBoost used session-held-out evaluation with physical normal/SYN data and controlled secondary attack classes.

Live hardware demo

The hero demonstration is a controlled SYN scenario against PI-001 inside an isolated team-owned lab.

Ubuntu VMware VM
Scapy attack generator
        |
        | controlled SYN traffic
        v
Raspberry Pi PI-001
        |
        | real network packets
        v
Windows Npcap + TShark
        |
        | normalized telemetry
        v
FastAPI + Aegis Hybrid Trust Engine
        |
        +--> Rules
        +--> XGBoost
        +--> LSTM-VAE
        +--> JSD
        |
        v
Trust + State + XAI + MITRE + Incident + Forensics
        |
        v
Controlled Remediation -> Recovery Verification -> Twin Resynchronization

In the live flow, a healthy Pi normally sits around the preferred 96-99 trust range. Under the controlled SYN scenario, packet behaviour diverges, trust collapses into the attack region, and recognised SYN behaviour can be mapped to MITRE ATT&CK T1498.001, Direct Network Flood. Recovery is accepted only after clean telemetry is observed again.

A useful way to describe the stack is:

Scapy generates the behaviour. TShark observes reality. Aegis interprets it.

System architecture

Browser
  |
  v
Next.js / Tailwind frontend
  |
  v
FastAPI backend
  |
  +--> Telemetry ingestion
  +--> Device behavioural twin
  +--> Hybrid intelligence engine
  |      +--> YAML rules
  |      +--> XGBoost
  |      +--> LSTM-VAE + attention
  |      +--> Per-feature JSD
  |
  +--> Trust Composer + state machine
  +--> MITRE mapping
  +--> Incident lifecycle
  +--> Forensic evidence and reports
  +--> Controlled remediation
  +--> Recovery verification

Physical finals topology

Windows host
Pi-facing adapter : 192.168.56.1/24
VM management     : 172.16.50.1/24

Raspberry Pi PI-001
eth0              : 192.168.56.20/24

Ubuntu VMware attacker
management NIC    : 172.16.50.10/24
attack NIC        : 192.168.56.10/24

The VM is used only for the narrow, authenticated and allowlisted attack-controller path. The protected Raspberry Pi does not need to run the heavy detection stack.

Project structure

.
├── app/
│   └── web/                         # Next.js frontend
├── services/
│   └── backend/
│       └── api/                     # FastAPI backend
├── model-store/
│   └── aegis-hybrid-trust/
│       └── v1/                      # active frozen model package
├── scripts/
│   ├── tshark_live.py               # Windows live telemetry adapter
│   ├── step4b_finals_train.py       # finals physical calibration/training
│   ├── run_demo_acceptance.py       # repeatable end-to-end acceptance
│   ├── finals_preflight.py          # hardware/system preflight
│   ├── validate_pi_sessions.py      # physical dataset validation
│   └── lab_vm/
│       ├── pi_syn_demo.py            # bounded SYN scenario generator
│       └── aegis_lab_agent.py        # authenticated VM controller
├── data/
│   ├── finals-capture/              # physical capture artifacts
│   └── reports/
├── doc/
│   ├── HARDWARE_DEMO_RUNBOOK.md
│   ├── STEP4_REAL_DATA_CAPTURE.md
│   ├── TECHNICAL_SOURCE_OF_TRUTH.md
│   └── FRONTEND_INTEGRATION_CONTRACT.md
└── README.md

Local development

Backend

cd services/backend/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Frontend

cd app/web
npm install
npm run dev

Open:

Frontend      http://localhost:3000
Backend docs  http://localhost:8000/docs
Health        http://localhost:8000/api/v1/health

Windows Raspberry Pi telemetry

The finals sensor path uses Npcap + TShark.

List interfaces first because the numeric interface index may change after reconnecting hardware:

python scripts\tshark_live.py --list-interfaces

Then start the Pi-facing sensor:

python scripts\tshark_live.py `
  --interface <interface-id> `
  --target-ip 192.168.56.20 `
  --api-url http://localhost:8000 `
  --device-id PI-001

Expected healthy state:

source_mode : live_hardware
sensor      : tshark_npcap
state       : HEALTHY
trust       : >= 95

Main API surface

GET  /api/v1/health
GET  /api/v1/fleet
POST /api/v1/telemetry/windows
GET  /api/v1/devices/{device_id}/state
GET  /api/v1/events/trust
GET  /api/v1/incidents
GET  /api/v1/system/capabilities
POST /api/v1/devices/{device_id}/remediate
POST /api/v1/demo/replay/pi_syn

FastAPI also exposes Swagger, ReDoc and OpenAPI at /docs, /redoc and /openapi.json.

Model lifecycle

The active release package is:

model-store/aegis-hybrid-trust/v1/

For finals physical calibration, use the dedicated trainer and validate outputs before replacing frozen artifacts. The repository keeps model checkpoints, baselines, intelligence configuration and application code separated so the inference contract remains auditable.

A typical verification path is:

python scripts\validate_pi_sessions.py --input data\finals-capture\pi_sessions.jsonl
python scripts\run_demo_acceptance.py --loops 20
python scripts\finals_preflight.py

Explainability and forensics

Aegis-Twin exposes more than a final label. The device state can include:

raw and canonical feature values

deviation from the learned baseline

rule evidence and matched conditions

XGBoost class probabilities

LSTM-VAE reconstruction/anomaly evidence

per-feature JSD drift

detector contributions to trust

known vs unknown classification state

MITRE ATT&CK mapping where supported

incident timeline and forensic snapshot

remediation and recovery progress

Unknown behavioural anomalies are intentionally kept separate from known attacks rather than being forced into a misleading MITRE label.

Incident and recovery lifecycle

HEALTHY
   |
   | behavioural divergence
   v
SUSPICIOUS / ATTACK
   |
   +--> explain evidence
   +--> classify known or unknown
   +--> MITRE map when supported
   +--> preserve forensic snapshot
   |
   v
OPERATOR REMEDIATION
   |
   v
RECOVERING
   |
   +--> clean window 1/3
   +--> clean window 2/3
   +--> clean window 3/3
   v
HEALTHY + TWIN RESYNCHRONIZED

The key design principle is simple:

Stopping an attack is not the same as proving recovery.

Scalability and real-world relevance

Aegis-Twin is designed as a software-first, retrofit-friendly security layer. Heavy inference does not need to run on the protected IoT endpoint, so constrained devices can remain lightweight while observation and intelligence are performed externally. The same architecture can be extended from one Pi to heterogeneous fleets by maintaining per-device or per-device-class behavioural baselines and trust states.

This makes the approach relevant to smart factories, campuses, hospitals, utilities, building-management systems and other environments where replacing an entire deployed IoT fleet is unrealistic.

Sustainability

The architecture is intended to work around existing devices rather than requiring them to be replaced. External observation, centralised intelligence and behavioural profiling make it possible to add a security and resilience layer to legacy or resource-constrained assets, supporting longer useful device lifecycles and reducing unnecessary hardware replacement.

Future work

The next research and engineering steps include:

scaling from a single physical endpoint to multi-device fleet learning

broader physical validation across heterogeneous IoT classes

additional known attack families and deliberately unseen attack evaluation

SIEM/SOC integration

policy-controlled automated containment with human approval for critical actions

long-horizon drift adaptation and baseline versioning

distributed edge collectors for multi-site deployments

Evaluation integrity

Aegis-Twin intentionally distinguishes between:

OBSERVATION   what happened on the physical network
INTELLIGENCE  what models and rules inferred
DECISION      how evidence became trust and state
RESPONSE      what constrained action was authorised
VERIFICATION  whether clean evidence proved recovery

Physical validation numbers, controlled ablation metrics and demo/replay behaviour should therefore be reported with their evaluation scope rather than mixed together as a single production-accuracy claim.

Final project statement

Aegis-Twin is an explainable, device-specific cyber-resilience digital twin that combines real packet observati