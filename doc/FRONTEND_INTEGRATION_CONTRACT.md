# Aegis-Twin Frontend Integration Contract

Contract stage: Step 1 (foundation and live telemetry). Last updated: 2026-09-03.

The backend is authoritative for security/model values. React must render returned values and must not calculate trust, detector percentages, rule results, canonical values, or provenance. Fields planned for later stages are clearly marked and must not be faked meanwhile.

## Transport

- Development backend: `http://localhost:8000`
- Frontend proxy: call relative `/api/v1/...`
- JSON content type: `application/json`
- Timestamps: timezone-aware ISO 8601 UTC
- Live updates: SSE, event name `trust`

## States and trust

| State | Meaning | Trust behavior |
| --- | --- | --- |
| `BOOTSTRAP` | Baseline/model initialization | presentation target 98 |
| `HEALTHY` | Clean telemetry | 96–99 |
| `SUSPICIOUS` | Material but unconfirmed divergence | 35–75 in current composer |
| `ATTACK` | Confirmed rule or sufficiently critical anomaly | below 30 |
| `RECOVERING` | Remediation requested; clean windows being checked | moves toward 97 |
| `STALE` | Capture loss or explicitly stale input | freezes last trust |

`trust` is an operational 0–100 score. It is not model accuracy.

## Source badges

Render `source_mode` exactly as:

| Value | Badge |
| --- | --- |
| `mock` | MOCK FLEET |
| `live_hardware` | LIVE HARDWARE |
| `recorded_replay` | RECORDED REPLAY |
| `xai_simulation` | XAI SIMULATION |

Use `sensor` as the secondary provenance label. An initial PI baseline seed reports `mock`/`aegis-simulator`; it becomes `live_hardware` only after real sensor ingestion.

## Endpoint inventory

### `GET /`

Returns `{"service":"aegis-twin-api","status":"ok"}`.

### `GET /api/v1/health`

Returns `{"status":"ok"}`. This checks the API process, not Pi reachability.

### `POST /api/v1/auth/login`

Compatibility placeholder only. It currently returns a message and must not be presented as completed authentication.

### `GET /api/v1/fleet`

Returns a compact array for fleet/map/search updates:

```json
[
  {
    "id": "PI-001",
    "name": "AEGIS Raspberry Pi",
    "sector": "Hardware Lab",
    "source": "pi",
    "source_mode": "recorded_replay",
    "sensor": "aegis-replay",
    "status": "Compromised",
    "trust": 5,
    "state": "ATTACK",
    "attack_type": "syn_flood",
    "confidence": 1.0,
    "updated_at": "2026-09-03T10:27:23Z"
  }
]
```

`source` is the device profile/legacy compatibility field. Always use `source_mode` for the visible provenance badge.

### `POST /api/v1/telemetry/windows`

Sensor-neutral ingestion. Accepts 1–20 points and both legacy and final source names.

```json
{
  "device_id": "PI-001",
  "source": "live_hardware",
  "sensor": "tshark_npcap",
  "session_id": "pi-20260903T102700Z-8437bc0f",
  "attack_job_id": "pi-syn-demo",
  "sequence_seconds": 20,
  "timestamp": "2026-09-03T10:27:00Z",
  "stale": false,
  "service_healthy": true,
  "points": [
    {
      "packet_size": 60.0,
      "iat": 0.001,
      "payload_entropy": 0.0,
      "flow_symmetry": 0.01,
      "syn_rate": 183.0,
      "syn_ack_rate": 2.0,
      "ack_rate": 1.0,
      "incomplete_ratio": 0.88,
      "handshake_completion_ratio": 0.12,
      "unique_sources": 1.0,
      "unique_destination_ports": 1.0,
      "rejected_connections": 0.0,
      "reset_connections": 0.0,
      "orig_packets": 700.0,
      "resp_packets": 5.0,
      "orig_bytes": 42000.0,
      "resp_bytes": 300.0,
      "connection_duration_mean": 0.0,
      "ssh_attempts": 0.0,
      "ssh_failures": 0.0,
      "capture_loss": 0.0
    }
  ]
}
```

All numbers must be finite and non-negative; ratios must be within `[0,1]`. Invalid input returns 422. Unknown device returns 404. Success returns the full prediction described below.

### `GET /api/v1/devices/{device_id}/state`

Returns the full latest prediction plus `name` and `sector`. Unknown device returns 404.

### `POST /api/v1/devices/{device_id}/simulate-attack`

Only valid for mock devices. Returns the full attacked prediction. A Pi request returns 409.

### `POST /api/v1/devices/{device_id}/remediate`

Returns:

```json
{
  "device_id": "DEV-001",
  "state": "RECOVERING",
  "target_trust": 97,
  "controller": {"stopped": true, "reason": "mock_generator_reset"},
  "prediction": {"state": "RECOVERING", "trust": 80.0}
}
```

For PI-001, `controller.stopped=false` and a reason such as `attack_controller_not_configured` is a real failure; the UI must not show successful containment.

### `POST /api/v1/demo/replay/{scenario}?speed=4`

Scenarios currently: `pi_syn`, `pi_normal`. Returns `{"scenario":"pi_syn","status":"started","speed":4.0}`. Resulting state always reports `source_mode=recorded_replay`.

### `GET /api/v1/events/trust`

SSE content type `text/event-stream`. Trust changes are emitted at most every 0.5 seconds and a comment heartbeat is sent after roughly 10 seconds without a version change.

```text
event: trust
data: {"version":42,"devices":[...]}
```

Reconnect with standard `EventSource`; replace the compact fleet array from `devices`.

## Full prediction shape

```json
{
  "device_id": "PI-001",
  "source": "recorded_replay",
  "source_mode": "recorded_replay",
  "sensor": "aegis-replay",
  "state": "ATTACK",
  "status": "ATTACK",
  "trust": 5.0,
  "risk": 0.9528,
  "attack_type": "syn_flood",
  "confidence": 1.0,
  "reconstruction_error": 171.20369,
  "latent_uncertainty": 0.258284,
  "jsd": 0.073051,
  "rule_risk": 1.0,
  "classifier_risk": 0.99726,
  "vae_risk": 1.0,
  "baseline_risk": 1.0,
  "attention_weights": [0.030085, 0.034399],
  "top_anomalies": [
    {"feature": "syn_rate", "score": 1.0, "direction": "high"}
  ],
  "current_features": {"syn_rate": 250.0},
  "baseline_features": {"syn_rate": 3.0},
  "raw_features": {"syn_rate": 324.0},
  "canonical_features": {"syn_rate": 250.0},
  "canonicalization_version": "aegis-canonicalization-v1",
  "canonicalization_applied": {
    "syn_rate": {"bucket": "severe_syn", "raw": 324.0, "canonical": 250.0}
  },
  "feature_deviations": {
    "syn_rate": {
      "baseline": 3.0,
      "observed": 250.0,
      "delta": 247.0,
      "normalized_deviation": 82.333333,
      "direction": "high"
    }
  },
  "jsd_by_feature": {"syn_rate": 0.137925},
  "rule": {
    "rule_id": "AEGIS-SYN-001",
    "name": "Raspberry Pi SYN Flood",
    "attack_type": "syn_flood",
    "severity": "critical",
    "matched": true,
    "risk": 1.0,
    "required_conditions": 3,
    "conditions": [
      {
        "feature": "syn_rate",
        "operator": ">=",
        "threshold": 50.0,
        "observed": 250.0,
        "raw_observed": 324.0,
        "passed": true
      }
    ],
    "matched_conditions": [
      {
        "feature": "syn_rate",
        "operator": ">=",
        "threshold": 50.0,
        "observed": 250.0,
        "raw_observed": 324.0,
        "passed": true
      }
    ],
    "failed_conditions": [],
    "mitre": {
      "technique_id": "T1498.001",
      "technique_name": "Direct Network Flood",
      "tactic": "Impact"
    },
    "response": {
      "action": "stop_registered_attack_job",
      "mode": "attack_controller_fallback"
    },
    "explanation": "Initial SYN traffic is high while handshake failures rise and successful completion collapses.",
    "version": "1.0.0"
  },
  "telemetry_quality": "good",
  "model_version": "aegis-hybrid-trust/v1",
  "baseline_version": "v1",
  "model_backends": {
    "vae": "pytorch-lstm-vae",
    "classifier": "xgboost",
    "drift": "per-feature-jsd",
    "rules": "aegis-rules-v1"
  },
  "timestamp": "2026-09-03T10:27:23Z"
}
```

Arrays/maps are shown shortened only for documentation readability; API responses contain the full supported feature set and 20 attention weights once a full sequence is buffered.

## Step 2 explainability additions

The existing state response is backward compatible and now also includes:

- `classifier`: four-class probability map, label, confidence, top-two margin, confidence status, backend, and model version;
- `temporal`: reconstruction error, threshold, normalized VAE risk, anomaly boolean, latent uncertainty, 20 attention weights, temporal importance, and reconstruction summary/availability;
- `feature_deviations`: baseline, raw and canonical observations/deltas, window mean, normalized deviation, direction, severity, and availability;
- `feature_availability` and available `jsd_by_feature` values;
- `detectors`, distinct `known_attack_risk` and `unknown_anomaly_score`;
- `detection_mode`, `classification`, and the complete `trust_calculation`.

New read-only/presentation endpoints are:

```text
GET  /api/v1/devices/{device_id}/explainability
GET  /api/v1/model/metrics
GET  /api/v1/mitre/scenarios
POST /api/v1/xai/scenarios/{scenario}?technique_id=T1046
```

Valid XAI scenario names are `normal`, `known_attack`, `unknown_anomaly`, and `mitre`. All return explicit `xai_simulation` provenance and use the same backend pipeline as runtime telemetry. Metrics must be labelled with their returned controlled synthetic/replay scope. Null confusion-matrix or per-class fields mean the frozen artifact did not contain them; the UI must not manufacture those values.

### Field ownership

| Fields | Meaning |
| --- | --- |
| `raw_features` | Raw measurement exactly as supplied by the adapter |
| `canonical_features`, `canonicalization_applied` | Canonical measurement plus auditable transformation metadata |
| `classifier`, `temporal`, `jsd`, `jsd_by_feature` | Model outputs |
| `feature_deviations`, `detectors`, `top_anomalies`, `trust_calculation` | Derived backend calculations |
| `model_version`, `baseline_version`, rule/config versions | Configuration metadata |
| XAI `scenario`, `provenance`, `deterministic` | Explicit simulation metadata |

### Step 2 scenario payload examples

Every `prediction` below has the complete shared shape documented in **Full prediction shape**. These discriminator examples show the exact fields the UI uses to distinguish all required scenarios; actual API responses include the full feature maps and all 20 attention values.

```json
{
  "healthy_pi": {"source_mode":"mock","sensor":"aegis-simulator","state":"HEALTHY","trust":98.45,"attack_type":"none","detection_mode":"normal","classification":{"type":"none","known":false,"mitre_status":"unmapped","mitre":null}},
  "known_syn_pi": {"source_mode":"recorded_replay","sensor":"aegis-replay","state":"ATTACK","trust":5.0,"attack_type":"syn_flood","detection_mode":"known_attack","rule":{"rule_id":"AEGIS-SYN-001","matched":true},"classification":{"type":"syn_flood","known":true,"mitre_status":"mapped","mitre":{"technique_id":"T1498.001","technique_name":"Direct Network Flood","tactic":"Impact"}}},
  "healthy_mock": {"source_mode":"mock","sensor":"aegis-simulator","state":"HEALTHY","trust":98.53,"attack_type":"none","detection_mode":"normal"},
  "known_mock_attack": {"source_mode":"mock","sensor":"aegis-simulator","state":"ATTACK","trust":5.0,"attack_type":"behavioral_drift","detection_mode":"known_attack","classification":{"type":"behavioral_drift","known":true,"mitre_status":"unmapped","mitre":null}},
  "unknown_behavioral_anomaly": {"source_mode":"xai_simulation","sensor":"aegis-xai-fixture","state":"ATTACK","trust":17.05,"attack_type":"unknown_behavioral_anomaly","detection_mode":"unknown_anomaly","unknown_anomaly_score":0.829459,"classifier":{"label":"normal","status":"confident_normal","known_attack_confident":false},"classification":{"type":"unknown_behavioral_anomaly","known":false,"mitre_status":"unmapped","mitre":null}},
  "mitre_simulation": {"scenario":"mitre","deterministic":true,"provenance":{"source_mode":"xai_simulation","sensor":"aegis-xai-fixture","mitre_scenario":{"technique_id":"T1046","demo_mode":"recorded_replay_optional_live"}},"prediction":{"state":"ATTACK","trust":5.0,"attack_type":"port_scan","detection_mode":"known_attack"}}
}
```

XAI envelopes returned by `POST /api/v1/xai/scenarios/{scenario}`:

```json
{
  "xai_normal": {"scenario":"normal","provenance":{"source_mode":"xai_simulation","sensor":"aegis-xai-fixture"},"deterministic":true,"prediction":{"state":"HEALTHY","trust":98.53,"attack_type":"none","detection_mode":"normal"},"calculation_steps":[{"step":"detector_normalization"},{"step":"known_unknown_decision"},{"step":"trust_composition"}]},
  "xai_known": {"scenario":"known_attack","provenance":{"source_mode":"xai_simulation","sensor":"aegis-xai-fixture"},"deterministic":true,"prediction":{"state":"ATTACK","trust":5.0,"attack_type":"syn_flood","detection_mode":"known_attack"},"calculation_steps":[{"step":"detector_normalization"},{"step":"known_unknown_decision"},{"step":"trust_composition"}]},
  "xai_unknown": {"scenario":"unknown_anomaly","provenance":{"source_mode":"xai_simulation","sensor":"aegis-xai-fixture"},"deterministic":true,"prediction":{"state":"ATTACK","trust":17.05,"attack_type":"unknown_behavioral_anomaly","detection_mode":"unknown_anomaly"},"calculation_steps":[{"step":"detector_normalization"},{"step":"known_unknown_decision"},{"step":"trust_composition"}]}
}
```

Model metrics response:

```json
{"available":true,"model_version":"aegis-hybrid-trust/v1","source":"synthetic-demo","metric_scope":"controlled synthetic and replay scenarios; not a production generalization claim","metrics":{"accuracy":1.0,"macro_f1":1.0,"syn_flood_recall":1.0,"held_out_sessions":6,"train_windows":720,"test_windows":240,"demo_loops":20,"demo_loops_passed":20,"demo_scenario_success_rate":100.0},"confusion_matrix":null,"per_class_metrics":null,"limitations":"Confusion matrix and per-class metrics are unavailable in the frozen artifact."}
```

## Step 1 scenario samples

These values are produced by the current deterministic software/replay path; they are not physical hardware claims.

| Scenario | Source mode | Expected backend result |
| --- | --- | --- |
| Healthy mock | `mock` | `HEALTHY`, trust 96–99, attack `none` |
| Attacked mock | `mock` | `ATTACK`, trust 5, `behavioral_drift`, four anomalous features |
| Recovering mock | `mock` | first response `RECOVERING`, trust 80; subsequent clean ticks reach healthy >=96 |
| Healthy Pi baseline seed | `mock` | `HEALTHY`, trust 96–99; not labelled live |
| Healthy Pi sensor input | `live_hardware` | result depends on actual measured clean values; target healthy >=95 |
| Pi suspicious | source of submitted data | `SUSPICIOUS`, trust 35–75 when divergence is material but YAML rule is not confirmed |
| Pi SYN attack | `live_hardware` or `recorded_replay` | `ATTACK`, trust below 30, `AEGIS-SYN-001`, `T1498.001` |
| Pi remediation | latest source | response includes real controller success/failure; no fake success |
| Pi recovered | latest source | after three clean windows, `HEALTHY`, trust >=96 |
| Stale Pi | latest source | explicit stale/capture loss produces `STALE` and frozen trust |
| Replay mode | `recorded_replay` | same scoring/SSE path, never live badge |

## Model validation artifact

The current file `model-store/aegis-hybrid-trust/v1/metrics.json` contains controlled synthetic/replay values:

```json
{
  "accuracy": 1.0,
  "macro_f1": 1.0,
  "syn_flood_recall": 1.0,
  "held_out_sessions": 6,
  "train_windows": 720,
  "test_windows": 240,
  "training_epochs": 8,
  "demo_loops": 20,
  "demo_loops_passed": 20,
  "demo_scenario_success_rate": 100.0,
  "metric_scope": "controlled synthetic and replay scenarios; not a production generalization claim"
}
```

The supported source for these metrics is now `GET /api/v1/model/metrics`. Do not hardcode them in React.

## Step 3 incident and recovery contract

The backend is authoritative for incidents, reports, remediation phases, recovery counters, and staleness. The frontend must never advance these phases on a timer.

```text
GET /api/v1/incidents?device_id=PI-001&status=OPEN&severity=CRITICAL&source_mode=live_hardware
GET /api/v1/incidents/{incident_id}
GET /api/v1/incidents/{incident_id}/timeline
GET /api/v1/incidents/{incident_id}/report
GET /api/v1/system/capabilities
```

`GET /api/v1/events/trust` retains `version` and `devices` and adds lightweight `operational_events`. Events include incident creation, report generation, remediation success/failure, recovery progress/verification, closure, stale, and live-again transitions.

### Finals payload samples A–L

```json
{
  "A_healthy_hardware": {"state":"HEALTHY","trust":98.1,"source_mode":"live_hardware","last_seen":"2026-09-03T12:00:00+00:00","stale_since":null,"active_incident_id":null},
  "B_syn_incident_created": {"state":"ATTACK","trust":5.0,"attack_type":"syn_flood","active_incident_id":"INC-20260903-0001","classification":{"known":true,"mitre":{"technique_id":"T1498.001","technique_name":"Direct Network Flood"}}},
  "C_forensic_ready": {"incident_id":"INC-20260903-0001","status":"OPEN","forensic_snapshot":{"source_mode":"recorded_replay","rule":{"rule_id":"AEGIS-SYN-001","matched":true},"raw_features":{"syn_rate":276.0},"canonical_features":{"syn_rate":250.0}},"report":{"status":"ready","report_ready":true,"report_id":"RPT-INC-20260903-0001","path":".../reports/incidents-v1/INC-20260903-0001.html"}},
  "D_remediation_requested": {"incident_id":"INC-20260903-0001","provider":"attack_controller_stop","phase":"APPLYING_POLICY","success":null,"started_at":"2026-09-03T12:00:03+00:00"},
  "E_containment_succeeded": {"incident_id":"INC-20260903-0001","provider":"attack_controller_stop","phase":"VERIFYING_RECOVERY","success":true,"provider_result":{"outcome":"stopped","job_id":"pi-syn-demo"}},
  "F_recovery_1_of_3": {"state":"RECOVERING","trust":80.0,"recovery_progress":{"clean_windows_required":3,"clean_windows_observed":1,"recovery_threshold":95}},
  "G_recovery_2_of_3": {"state":"RECOVERING","trust":97.0,"recovery_progress":{"clean_windows_required":3,"clean_windows_observed":2,"recovery_threshold":95}},
  "H_recovery_verified": {"state":"HEALTHY","trust":97.0,"incident":{"status":"CLOSED","recovery_trust":97.0,"recovery_verification":{"status":"verified","clean_windows_observed":3,"clean_windows_required":3}}},
  "I_remediation_failure": {"incident_id":"INC-20260903-0001","phase":"FAILED","success":false,"provider_result":{"outcome":"controller_unavailable"},"state":"ATTACK"},
  "J_stale_hardware": {"state":"STALE","telemetry_quality":"stale","last_seen":"2026-09-03T12:00:00+00:00","seconds_since_last_seen":4.2,"stale_since":"2026-09-03T12:00:04.2+00:00"},
  "K_unknown_incident": {"status":"OPEN","severity":"CRITICAL","attack_type":"unknown_behavioral_anomaly","known":false,"mitre":null,"mitre_status":"unmapped","forensic_snapshot":{"unknown_anomaly_score":0.829459}},
  "L_incident_list": {"count":1,"incidents":[{"incident_id":"INC-20260903-0001","device_id":"PI-001","status":"OPEN","severity":"CRITICAL","source_mode":"live_hardware","minimum_trust":5.0,"current_trust":5.0}]}
}
```

Paths and timestamps are illustrative; detector values and lifecycle state must come from the backend. Render `recorded_replay`, `xai_simulation`, and `live_hardware` exactly from provenance.

## Explicitly deferred contracts

The following requested samples/fields are not implemented in Step 1 and must not be simulated in the frontend:

- confusion-matrix details remain unavailable until a future frozen artifact contains them.

This document will be expanded at each stage until all fourteen final scenario payloads are concrete backend outputs.
