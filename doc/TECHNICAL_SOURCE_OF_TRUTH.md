# Aegis-Twin Technical Source of Truth

Last updated: 2026-09-03

`plan.md` is the frozen product specification. This document describes the implementation after Step 1; it does not compete with the plan.

## Runtime architecture

```text
Npcap -> TShark -> scripts/tshark_live.py --+
Zeek -> scripts/zeek_tail.py ---------------+-> normalized TelemetryWindow
recorded replay ----------------------------+          |
mock simulator -----------------------------+          v
                                                validation/canonicalization
                                                          |
                                                          v
                                    YAML rules + XGBoost + LSTM-VAE + JSD
                                                          |
                                                          v
                                             HybridTrustService -> SSE/UI
```

The final Windows hardware path is Npcap + TShark. Zeek remains an alternate Linux sensor. All adapters submit the same API model, and inference does not branch on the capture implementation.

## Source provenance

The ingestion API accepts current public source modes plus legacy aliases:

| Submitted `source` | Public `source_mode` | Meaning |
| --- | --- | --- |
| `mock` | `mock` | Generated mock digital twin |
| `pi` or `live_hardware` | `live_hardware` | Packet-derived physical telemetry |
| `replay` or `recorded_replay` | `recorded_replay` | Recorded/deterministic replay |
| `xai_simulation` | `xai_simulation` | Explicit explainability simulation |

Predictions also expose `sensor`, for example `tshark_npcap`, `zeek`, `aegis-replay`, or `aegis-simulator`. Replay never reports itself as live hardware.

## Sampling contract

- Telemetry interval: 1 second.
- Sequence buffer: 20 samples.
- Temporal context: approximately 20 seconds.
- API windows may contain 1–20 points. The service maintains the rolling 20-point device buffer.

## Feature contract

`orig` means traffic sent toward PI-001; `resp` means traffic sent by PI-001. Rates are divided by the configured interval, normally one second.

| Feature | Unit / formula in one interval | Zero-packet behavior | Abnormal direction | Processing |
| --- | --- | --- | --- | --- |
| `packet_size` | bytes; mean `frame.len` of relevant packets | `0` | topology-dependent | raw unless configured later |
| `iat` | seconds; mean non-negative delta between ordered packet timestamps | sample interval (`1.0`) | very low or large drift | raw |
| `payload_entropy` | normalized `[0,1]`; unavailable in the TShark critical path | `0` | device-specific drift | raw; not required for Pi SYN detection |
| `flow_symmetry` | `min(orig_packets,resp_packets)/max(...)` | `1` | low | raw |
| `syn_rate` | inbound TCP packets with `SYN=1, ACK=0` / seconds | `0` | high | severe-SYN bucket eligible |
| `syn_ack_rate` | outbound TCP packets with `SYN=1, ACK=1` / seconds | `0` | low relative to SYN | raw |
| `ack_rate` | inbound TCP packets with `ACK=1, SYN=0` / seconds | `0` | low relative to SYN | raw |
| `incomplete_ratio` | `1 - min(initial_SYN,SYN_ACK,final_ACK)/initial_SYN` | `0` when no initial SYN | high | severe-SYN bucket eligible |
| `handshake_completion_ratio` | `min(initial_SYN,SYN_ACK,final_ACK)/initial_SYN` | `1` when no initial SYN | low | severe-SYN bucket eligible |
| `unique_sources` | distinct inbound source IP count | `0` | high | raw |
| `unique_destination_ports` | distinct inbound Pi destination port count | `0` | high | raw |
| `rejected_connections` | outbound Pi RST packet count | `0` | high | raw approximation |
| `reset_connections` | relevant TCP RST packet count | `0` | high | raw |
| `orig_packets` | packet count toward Pi | `0` | high/asymmetric | raw |
| `resp_packets` | packet count from Pi | `0` | low relative to originator | raw |
| `orig_bytes` | sum of `frame.len` toward Pi | `0` | high/asymmetric | raw |
| `resp_bytes` | sum of `frame.len` from Pi | `0` | low relative to originator | raw |
| `connection_duration_mean` | seconds; adapter-specific completed-flow mean | `0` | device-specific | TShark Step 1 reports unavailable as `0` |
| `ssh_attempts` | inbound initial SYN count with destination port 22 | `0` | high | raw |
| `ssh_failures` | outbound Pi RST count with source port 22 | `0` | high | raw approximation |
| `capture_loss` | normalized `[0,1]` capture quality indicator | `0` while capture is healthy | high | `>=0.25` forces `STALE` |

All values must be finite and non-negative. Ratio features must be within `[0,1]`. Malformed telemetry is rejected with HTTP 422; invalid values never propagate into trust.

## Canonicalization

Configuration is versioned in `model-store/aegis-hybrid-trust/v1/canonicalization.json`. The current canonicalizer changes only a jointly severe SYN region:

```text
raw syn_rate >= 100
AND raw incomplete_ratio >= 0.75
AND raw handshake_completion_ratio <= 0.25
```

That region maps to calibrated values `250`, `0.95`, and `0.05`. This absorbs scheduling jitter without inventing an attack: all three raw conditions must already demonstrate severe real behavior. Each prediction exposes `raw_features`, `canonical_features`, `canonicalization_version`, and `canonicalization_applied`. Normal telemetry is not quantized.

## YAML rule engine

Rules live at `rules/aegis_rules.yaml` and are validated at backend startup. Invalid YAML, duplicate IDs, unknown features, unsupported operators, non-finite thresholds, or impossible required-condition counts fail with readable diagnostics.

`AEGIS-SYN-001` requires all of:

- `syn_rate >= 50`;
- `incomplete_ratio >= 0.65`;
- `handshake_completion_ratio <= 0.45`.

It maps to MITRE ATT&CK `T1498.001`, Direct Network Flood, tactic Impact. Predictions expose rule ID, matched/failed conditions, raw/canonical observed values, thresholds, risk, response policy, explanation, and version.

The prior deterministic port-scan and SSH checks are also represented in the same YAML as `AEGIS-SCAN-001` and `AEGIS-SSH-001`; they are retained for compatibility but are not additional physical finals requirements.

## Step 2 hybrid intelligence and trust composition

`HybridTrustEngine.score` is the shared inference path for mock, live, replay, and XAI sources. It now emits complete classifier probabilities, max-probability and margin confidence semantics, temporal reconstruction evidence, per-feature JSD availability, raw/canonical baseline deltas, and a deterministic anomaly ranking.

Known attacks require a matched YAML rule or a confident known classifier result with supporting behavioral evidence. Unknown behavioral anomalies require no matched known rule, no confident known classifier class, and a weighted novelty score at or above `0.72`:

```text
unknown = 0.40 * temporal + 0.25 * JSD + 0.35 * baseline deviation
```

Unknown results use `unknown_behavioral_anomaly`, `detection_mode=unknown_anomaly`, and `mitre_status=unmapped`. The XAI scenario metadata may name a simulated ATT&CK scenario, but does not falsely turn an unknown model result into an ATT&CK classification.

`TrustComposer` is the single state/trust authority. Pi profile risk is `0.50*rule + 0.30*classifier + 0.15*VAE + 0.05*JSD`; mock risk is `0.45*baseline + 0.35*VAE + 0.20*JSD`. Its response includes every normalized input, weight, contribution, selected risk, EWMA decision, state constraint, formula, and final trust.

Pi entropy remains outside `PI_FEATURES`. TShark explicitly reports entropy and connection-duration mean as unavailable; connection duration is canonicalized to its baseline only for inference, while its raw zero and availability reason remain in the evidence payload.

The eight-scenario presentation catalog is versioned in `rules/mitre_scenarios.yaml`. Only T1498.001 has a required live-hardware demo mode; T1046 and T1110.001 permit replay or live input, and the remaining scenarios are explicitly simulation proofs of concept.

## Trust contract retained in Step 2

- Healthy devices: 96–99 preferred and at least 95 required.
- Confirmed attack: trust below 30; confirmed rules bypass normal EWMA delay.
- Suspicious: 35–75 under the current presentation-safe composer.
- Recovering: requires three clean Pi windows before returning to healthy.
- Stale: freezes the last trust instead of presenting missing telemetry as compromise.

The single trust path remains `HybridTrustEngine.score`; mock, live hardware, Zeek, and replay do not implement separate frontend formulas.

## API

- `POST /api/v1/telemetry/windows`
- `GET /api/v1/devices/{device_id}/state`
- `POST /api/v1/devices/{device_id}/simulate-attack`
- `POST /api/v1/devices/{device_id}/remediate`
- `POST /api/v1/demo/replay/{scenario}`
- `GET /api/v1/events/trust`
- `GET /api/v1/fleet`
- `GET /api/v1/devices/{device_id}/explainability`
- `GET /api/v1/model/metrics`
- `GET /api/v1/mitre/scenarios`
- `POST /api/v1/xai/scenarios/{scenario}` (`normal`, `known_attack`, `unknown_anomaly`, or `mitre`)
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{incident_id}`
- `GET /api/v1/incidents/{incident_id}/timeline`
- `GET /api/v1/incidents/{incident_id}/report`
- `GET /api/v1/incidents/{incident_id}/report.pdf`
- `POST /api/v1/incidents/{incident_id}/assign`
- `POST /api/v1/incidents/{incident_id}/acknowledge`
- `POST /api/v1/incidents/{incident_id}/notes`
- `GET /api/v1/incidents/{incident_id}/notes`
- `POST /api/v1/incidents/{incident_id}/email-report`
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`, `GET /api/v1/auth/users`
- `GET /api/v1/system/capabilities`

See `doc/FRONTEND_INTEGRATION_CONTRACT.md` for payloads.

## Windows TShark adapter

`scripts/tshark_live.py` resolves TShark safely, binds only to the configured interface/private Pi target, parses packet fields without shell invocation, derives one-second features, submits explicit provenance, records labelled JSONL, retries temporary API failures, reconnects an exited capture, and terminates cleanly on Ctrl+C. Missing TShark is a clear fatal diagnostic; it never substitutes mock telemetry.

## Step 3 closed-loop resilience architecture

Step 2 predictions remain the detection authority. When a prediction first enters `ATTACK` below trust 30, `IncidentService` creates exactly one active SQLite incident for that device, freezes the entire prediction as `forensic_snapshot`, and generates one deterministic `INC-YYYYMMDD-NNNN.html` report. Repeated samples update current/minimum trust but do not create reports or incidents every second.

Device state and incident status remain separate. Incidents progress through `OPEN`, `CONTAINMENT_REQUESTED`, `CONTAINED`, `RECOVERING`, and immediate verified closure (`RECOVERY_VERIFIED` timeline event followed by `CLOSED`). A later attack after closure creates a new incident.

Remediation uses capability-reporting providers. Live hardware uses authenticated, allowlisted `attack_controller_stop`; replay uses `replay_stop`; mock devices use `mock_generator_reset`. Network isolation is explicitly unavailable until configured. Requested, started, completed, failed, and recovery-verified are distinct facts. Attack-contaminated temporal samples are cleared only after a successful provider result and after the forensic snapshot is persisted.

Recovery requires the configured number of consecutive clean hybrid observations, default three. A clean observation has valid telemetry, no matched known rule, no accepted malicious classifier result, no critical unknown score, and a `RECOVERING` or `HEALTHY` device result. An anomalous observation resets progress. The incident closes only when all clean windows are observed and trust is at least 95.

Wall-clock staleness applies only after actual `live_hardware` telemetry has been observed. After `AEGIS_TELEMETRY_STALE_SECONDS`, the last trust freezes and the device becomes `STALE`. Fresh telemetry re-enters full inference; it is not assumed healthy.

Persistent incident documents live in `data/aegis_incidents_v1.db`; idempotent HTML reports live under `reports/incidents-v1/`. Both paths are configurable. A report write failure is recorded on the incident and never crashes telemetry inference.

## Model package and step boundary

`model-store/aegis-hybrid-trust/v1/` contains baselines, VAE checkpoints, XGBoost, calibration, metrics, manifest, canonicalization, and intelligence thresholds. Step 3 surrounds this frozen model with incident persistence, forensics, remediation, recovery, and staleness. Real-dataset training/calibration remains Step 4. Hardware results may only be reported after physical acceptance.

## Step 3.5 enterprise workflow

Authentication is native Windows/Python and SQLite-backed. Passwords use salted `scrypt`; only password hashes and SHA-256 session-token hashes are persisted. Opaque bearer sessions are revocable and expire after `AEGIS_AUTH_TOKEN_HOURS`. The first account must be ADMIN, after which only an authenticated ADMIN may create users. Roles are deliberately limited to ADMIN, ASSET_OWNER, and SME_VENDOR.

All incident list/detail/timeline/report/assignment/note/email endpoints are protected. ADMIN sees all incidents. Other roles see only the incident currently assigned to them; an assigned ASSET_OWNER may delegate to an active SME_VENDOR. Assignment and reassignment histories, acknowledgement, notes, and email status updates are persisted as incident timeline events. Notes have no mutation or deletion operation.

Assignment is committed before report refresh and SMTP delivery. SMTP is optional and disabled by default. DISABLED/FAILED delivery never invalidates assignment. Retry reuses a current report and sends only to the persisted active assignee. Configuration is environment-only and capabilities never expose credentials.

Forensics retain the existing deterministic HTML and add an idempotent ReportLab PDF generated directly from the persisted incident and frozen forensic snapshot. HTML and PDF use the same incident ID. PDF failures are isolated and recorded as `pdf_status=failed`; detection, remediation, and HTML evidence continue.

This step does not alter telemetry schemas, canonicalization, rules, trust composition, TShark/Npcap capture, attack-controller topology, replay, or the model package. No container, external database, Redis, cloud identity, or browser-print dependency was introduced.
