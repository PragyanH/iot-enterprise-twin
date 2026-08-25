# Aegis-Twin Technical Source of Truth

Last updated: 2026-08-25

This document is the canonical technical reference for the repository at
D:\projects\iot-enterprise-twin. It describes the current product architecture,
module layout, API contract, data flow, operational model, Docker setup, and the
persistent model/artifact strategy.

This document supersedes the older Streamlit-only architecture notes and reflects
the current split frontend/backend project structure.

## 1. Executive summary

Aegis-Twin is an AI-driven cybersecurity digital twin platform for enterprise and
industrial IoT fleets. The system models expected device behavior, scores
operation confidence, and surfaces anomaly information to operators through a web
frontend.

The current project structure separates responsibilities into two main layers:

- Frontend: Next.js + Tailwind in app/web
- Backend: FastAPI service in services/backend/api

The application is designed around a residual architecture where the browser does
not talk directly to a shared Python process. Instead, the frontend calls the
backend through a Next.js API middleware proxy, and the backend exposes structured
REST endpoints and Swagger/OpenAPI documentation.

The app concept remains aligned with the original Aegis digital-twin workflow:

1. Maintain a baseline for each device.
2. Observe operational telemetry.
3. Run model inference through an LSTM autoencoder.
4. Compute anomaly metrics and trust score.
5. Display fleet health in a dashboard.
6. Allow report generation and operational response workflows.

## 2. Current repository layout

```text
.
├── apps/
│   └── web/                        # Next.js frontend
│       ├── src/
│       ├── package.json
│       ├── tailwind.config.ts
│       ├── next.config.mjs
│       └── Dockerfile
├── services/
│   └── backend/
│       ├── api/                    # FastAPI backend service
│       │   ├── app/
│       │   ├── requirements.txt
│       │   └── Dockerfile
│       └── legacy/                # legacy Streamlit files removed from active path
├── model-store/
│   └── aegis-lstm-autoencoder/
│       └── v1/
├── infra/
│   └── docker/
│       └── README.md              # infrastructure placeholders and rationale
├── scripts/
│   └── README.md                  # operational automation expectations
├── data/
│   ├── reports/
│   └── uploads/
├── reports/
├── doc/
│   ├── TECHNICAL_SOURCE_OF_TRUTH.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── model-store/
```

## 3. Frontend architecture

### Frontend stack

- Next.js 14
- React 18
- Tailwind CSS
- TypeScript
- App Router

### Frontend responsibilities

The frontend is responsible for:

- rendering the fleet overview and operator dashboard
- displaying device status cards and summary metrics
- consuming backend endpoints through the Next.js middleware proxy
- enforcing a single color palette source through Tailwind CSS variables
- presenting API status and operational health information

### Theme configuration

The five-color palette is centralized in one file:

- app/web/src/app/globals.css

The palette is declared as CSS variables and consumed by the Tailwind theme in:

- app/web/tailwind.config.ts

This makes palette changes easy and centralized.

## 4. Backend architecture

### Backend stack

- FastAPI
- Pydantic
- Python 3.11
- OpenAPI/Swagger generated automatically

### Backend responsibilities

The backend handles:

- fleet data routes
- health checks
- authentication hooks
- future model inference endpoints
- operational analytics and trust-score services
- future device telemetry processing

### Backend package layout

```text
services/backend/api/app/
├── api/
│   └── v1/
│       ├── routes/
│       │   ├── auth.py
│       │   ├── fleet.py
│       │   ├── health.py
│       │   └── __init__.py
│       └── __init__.py
├── core/
│   └── config.py
├── db/
│   └── sqlite/
│       └── auth.py
├── ml/
├── models/
├── schemas/
├── services/
├── main.py
└── __init__.py
```

This is the convention used for a clean Python service structure.

## 5. API contract and documentation

The FastAPI app is defined in:

- services/backend/api/app/main.py

It exposes OpenAPI automatically at:

- http://localhost:8000/docs
- http://localhost:8000/redoc
- http://localhost:8000/openapi.json

Current routes include:

- GET /api/v1/health
- GET /api/v1/fleet
- POST /api/v1/auth/login
- GET /

These are documented using route summary and description metadata so Swagger shows
clean API documentation to new developers and operators.

## 6. Middleware and cross-localhost communication

The frontend and backend are intentionally separated by localhost and port. The
browser cannot directly call another local service without CORS or a proxy.

The solution is the Next.js middleware in:

- app/web/src/middleware.ts

This middleware catches requests that start with /api/ and rewrites them to the
backend service URL.

Example:

- Browser request: /api/v1/fleet
- Middleware target: http://localhost:8000/api/v1/fleet

This avoids browser CORS issues and keeps the frontend and backend separated cleanly.

## 7. Docker and service orchestration

The compose file is:

- docker-compose.yml

It runs two services:

- api
- web

The critical runtime configuration is:

- backend port 8000
- frontend port 3000
- backend URL passed to the frontend as NEXT_PUBLIC_API_URL or via middleware
- CORS configured in the FastAPI app

### Why the earlier compose command failed

The failure was caused by a combination of environment and wiring issues:

1. The backend build context had drifted from the actual directory structure.
2. The project root was not aligned with the active backend location.
3. The frontend did not yet proxy API requests to the backend.
4. The backend did not have CORS configuration enabled for a split frontend/backend runtime.
5. The host environment itself lacked a running Docker daemon in this session, which prevented runtime validation here.

These issues were corrected by:

- moving the active backend under services/backend/api
- updating the compose build context
- exposing backend and frontend ports correctly
- enabling CORS in FastAPI
- adding the middleware proxy in the frontend

## 8. Data and persistence strategy

The project keeps user credentials in SQLite and uses app-local volumes for data and reports.

Relevant directories:

- data/
- reports/
- uploads/

The old Streamlit-era session state and in-memory-only state were replaced by a more conventional service-oriented structure in which the API and frontend communicate through HTTP rather than a shared in-process UI state store.

## 9. Model-store and digital twin model definition

The model artifacts live in:

- model-store/aegis-lstm-autoencoder/v1/

This directory is the versioned storage location for the Aegis LSTM autoencoder model used to detect behavioral drift.

### What this is

It represents the trained neural network artifact used to model normal device behavior and identify anomalies by reconstruction error and divergence from expected signatures.

### Purpose

The model store separates application code from trained assets so the system can:

- swap model versions cleanly
- keep checkpoints outside the Python service code
- support training and deployment workflows without mixing artifacts into the app package

### How model updates are handled

To train or swap a model:

1. Prepare data in the expected feature format.
2. Train the LSTM autoencoder.
3. Save the trained weights and metadata into model-store/aegis-lstm-autoencoder/v1/.
4. Update the load path in the backend model service.
5. Restart the backend service.

## 10. Why scripts and infra/docker are empty

### scripts

The scripts directory is reserved for operational automation such as:

- model training jobs
- data validation utilities
- ETL helpers
- deployment bootstraps
- smoke tests
- maintenance tools

At the moment it is intentionally empty because the project is still in migration and those tasks have not yet been added.

### infra/docker

This directory is reserved for reusable Docker support artifacts, including:

- custom Docker service assets
- healthcheck scripts
- container-specific configuration
- environment templates
- deployment wrappers

It is empty because the project-level orchestration is currently handled by the root docker-compose.yml and no service-specific Docker assets have been created yet.

## 11. Operational flow

The user experience is now structured as:

```text
User opens browser on localhost:3000
  |
  v
Next.js app renders dashboard
  |
  v
Middleware rewrites /api/* calls to backend on localhost:8000
  |
  v
FastAPI routes return JSON and telemetry metadata
  |
  v
Frontend renders refreshed fleet and device information
```

## 12. Current implementation status

This repository is now in a migrated, split-architecture state with:

- a clean Next.js frontend
- a clean FastAPI backend
- a centralized theme configuration
- OpenAPI documentation enabled
- middleware-based API routing
- Docker orchestration at the root
- model artifacts separated in model-store

The remaining work is to port the legacy business logic from the original Streamlit code into the new backend service layer in a production-ready manner.

## 13. Recommended conventions

- Keep all Python runtime logic under services/backend/api
- Keep the UI under app/web
- Keep model checkpoints under model-store
- Keep deployment and runtime support in infra/docker and docker-compose.yml
- Keep operational automation scripts under scripts
- Update this document whenever the architecture changes

Per rerun, it:

1. Resolves the selected device and baseline vector.
2. Applies deferred remediation reset state if present.
3. Applies deferred attack slider updates if present.
4. Initializes per-device slider keys:
   - `pkt_<dev_id>`
   - `iat_<dev_id>`
   - `ent_<dev_id>`
   - `sym_<dev_id>`
5. Renders the sidebar controls.
6. Reads current slider values.
7. Creates the model input tensor.
8. Runs autoencoder inference.
9. Computes MSE, per-feature reconstruction errors, JSD, and Trust Score.
10. Updates history buffers and device health state.
11. Displays status header, alert/remediation UI, charts, packet stream, math
    panel, and threat log.
12. If live scan is enabled, sleeps for one second and calls `st.rerun()`.

## 7. Device Registry

The canonical fixed registry is in `registry.py`. Each device has:

- `name`: user-visible device name.
- `type`: device class.
- `sector`: site or sector identifier.
- `baseline`: four normalized traffic features.
- `icon`: display icon.
- `lat`, `lon`: geospatial coordinates.

Canonical devices:

| ID | Name | Type | Sector | Baseline | Latitude | Longitude |
| --- | --- | --- | --- | --- | --- | --- |
| `DEV-001` | `AEGIS-PUMP-01` | Pump | `1` | `[0.4, 0.5, 0.3, 0.6]` | `12.9026` | `77.5001` |
| `DEV-002` | `Assembly Arm` | Robotic Arm | `2` | `[0.6, 0.3, 0.7, 0.5]` | `12.9035` | `77.5012` |
| `DEV-003` | `Grid Node 0X` | Smart Grid Node | `3` | `[0.3, 0.8, 0.4, 0.5]` | `12.9020` | `77.4990` |
| `DEV-004` | `Cryo-Storage A` | Bio-Storage Fridge | `4` | `[0.2, 0.6, 0.2, 0.8]` | `12.9045` | `77.5005` |
| `DEV-005` | `Mixer V-12` | Chemical Mixer | `5` | `[0.5, 0.5, 0.6, 0.4]` | `12.9015` | `77.5015` |
| `DEV-006` | `Security Cam 1` | Camera | `6` | `[0.8, 0.2, 0.4, 0.9]` | `12.9030` | `77.4985` |
| `DEV-007` | `Security Cam 2` | Camera | `7` | `[0.8, 0.2, 0.3, 0.8]` | `12.9022` | `77.5025` |
| `DEV-008` | `Coolant Pump` | Pump | `8` | `[0.5, 0.4, 0.4, 0.6]` | `12.9050` | `77.4995` |
| `DEV-009` | `Welding Arm` | Robotic Arm | `9` | `[0.7, 0.2, 0.8, 0.4]` | `12.9010` | `77.5000` |
| `DEV-010` | `Main Grid Relay` | Smart Grid Node | `7-G` | `[0.4, 0.7, 0.5, 0.6]` | `12.9038` | `77.4975` |

Feature order for every baseline:

1. Packet Size
2. Inter-Arrival Time
3. Payload Entropy
4. Flow Symmetry

Important distinction:

- `registry.py` contains the canonical registry with coordinates.
- `app.py` currently overwrites the imported registry with random `Sensor Node`
  entries and no coordinates. This should be treated as a bug or abandoned
  earlier code, not as the source of truth.

## 8. Session State Model

The application uses `st.session_state` as the main runtime state store.

Defaults are defined in `registry.SESSION_DEFAULTS`:

| Key | Type/shape | Purpose |
| --- | --- | --- |
| `page` | string | Current route, usually `"fleet"` or `"dashboard"` |
| `active_device` | string or `None` | Selected device ID |
| `device_health` | dict | Device ID to `"Healthy"` or `"Compromised"` |
| `packet_history` | pandas DataFrame | Recent synthetic packet rows |
| `threat_log` | list[dict] | Recent threat events for current view |
| `remediation_log` | list[dict] | Successful remediation actions shown on fleet page |
| `audit_logs` | list[dict] | Audit entries shown on fleet page |
| `remediation_locked` | bool | Disables controls while remediation is running |
| `attack_step` | dict | Per-device simulated attack progression |
| `math_mode_active` | bool | Controls display of live math/engine panel |
| `jsd_history` | list[float], length 10 | Sparkline data |
| `pulse_mse_history` | list[float], length 30 | Neural pulse MSE trend |
| `pulse_jsd_history` | list[float], length 30 | Neural pulse JSD trend |
| `reconstruction_errors_history` | list[list[float]] | Per-feature MSE history, 4 buffers of length 20 |
| `authenticated` | bool | Login state |
| `user_email` | string or `None` | Authenticated user's email |
| `login_error` | string or `None` | Latest login/register error |
| `password_visible` | bool | Password input visibility toggle |
| `register_mode` | bool | Login vs registration mode |
| `last_alert_sent` | dict | Per-device report/email cooldown timestamps |

Additional keys initialized directly in `app.py` before `SESSION_DEFAULTS`:

| Key | Purpose |
| --- | --- |
| `phone_activity_sparkline` | Legacy/unused phone activity trend |
| `live_metrics` | Legacy/unused aggregate metric dict |
| `sensitivity` | Legacy/unused numeric setting |
| `simulate_attack` | Legacy/unused attack flag |
| `PHONE` in `device_health` | Legacy/unused health entry |

Per-device widget keys created in `dashboard.py`:

| Pattern | Purpose |
| --- | --- |
| `pkt_<dev_id>` | Packet Size slider value |
| `iat_<dev_id>` | Inter-Arrival Time slider value |
| `ent_<dev_id>` | Payload Entropy slider value |
| `sym_<dev_id>` | Flow Symmetry slider value |
| `scan_<dev_id>` | Live Scan Mode toggle |
| `attack_<dev_id>` | Launch Attack button key |
| `remed_<dev_id>` | Remediate Device button key |
| `clear_<dev_id>` | Clear View Log button key |
| `math_toggle_<dev_id>` | Math panel toggle button key |

Important current-code caveat:

`app.py` initializes `packet_history` as a list before applying
`SESSION_DEFAULTS`. Because defaults are only applied when keys are absent,
the canonical DataFrame default from `registry.py` will not replace that list.
The normal map-click path resets it to a DataFrame, but the initialization order
is fragile.

## 9. Digital Twin Model

File: `model.py`

The model is a PyTorch LSTM autoencoder implemented in three classes:

| Class | Responsibility |
| --- | --- |
| `Encoder` | Compresses a packet sequence into a latent vector |
| `Decoder` | Reconstructs the packet sequence from the latent vector |
| `LSTMAutoencoder` | Wraps encoder and decoder and exposes reconstruction error |

Model constants:

| Constant | Value | Meaning |
| --- | --- | --- |
| `INPUT_FEATURES` | `4` | Packet Size, IAT, Payload Entropy, Flow Symmetry |
| `SEQ_LEN` | `10` | Ten packets/time steps per sequence |
| `HIDDEN_SIZE` | `64` | LSTM hidden dimension |
| `LATENT_SIZE` | `32` | Bottleneck dimension |
| `NUM_LAYERS` | `2` | Number of stacked LSTM layers |
| `DROPOUT` | `0.2` | Dropout between LSTM layers |

Architecture:

```text
Input tensor: (batch, 10, 4)
  |
  v
Encoder:
  LSTM(input_size=4, hidden_size=64, num_layers=2, batch_first=True)
  final hidden state from last layer
  Linear(64 -> 32)
  |
  v
Latent vector: (batch, 32)
  |
  v
Decoder:
  Linear(32 -> 64)
  repeat across sequence length 10
  LSTM(input_size=64, hidden_size=64, num_layers=2, batch_first=True)
  Linear(64 -> 4)
  |
  v
Reconstructed tensor: (batch, 10, 4)
```

Parameter count from local inspection:

| Part | Parameters |
| --- | --- |
| Encoder | 53,280 |
| Decoder | 68,932 |
| Total | 122,212 |

Important operational detail:

The repository does not include a training script, dataset, validation pipeline,
or saved model checkpoint. `app.py` constructs `LSTMAutoencoder()` with random
initial weights and sets it to eval mode. Therefore, the ML output should be
treated as a dashboard/simulation signal, not a calibrated production anomaly
detector.

`LSTMAutoencoder.reconstruction_error(x)`:

- Calls `self.forward(x)` inside `torch.no_grad()`.
- Computes `F.mse_loss(x_hat, x, reduction="none")`.
- Averages across sequence and feature dimensions.
- Returns one MSE value per sample as shape `(batch,)`.

## 10. Scoring Engine

File: `engine.py`

The scoring engine has two public functions:

```python
calculate_jsd(p: np.ndarray, q: np.ndarray) -> float
calculate_trust_score(reconstruction_error: float, jsd_value: float) -> float
```

### Jensen-Shannon Divergence

`calculate_jsd(p, q)`:

1. Converts both inputs to NumPy float arrays.
2. Requires matching shapes.
3. Rejects negative values.
4. Normalizes each vector by its sum.
5. Builds mixture distribution `m = 0.5 * (p + q)`.
6. Computes `0.5 * (entropy(p, m, base=2) + entropy(q, m, base=2))`.
7. Clips the result to `[0.0, 1.0]`.

The code assumes each vector has a positive sum. Zero-sum vectors are not
explicitly guarded and may produce invalid numeric behavior.

### Trust Score

Constants:

| Constant | Value | Meaning |
| --- | --- | --- |
| `MSE_THRESHOLD` | `0.10` | MSE above this starts reducing trust |
| `JSD_THRESHOLD` | `0.30` | JSD above this starts reducing trust |
| `MSE_PENALTY_SCALE` | `200` | Trust points deducted per unit MSE above threshold |
| `JSD_PENALTY_SCALE` | `100` | Trust points deducted per unit JSD above threshold |

`calculate_trust_score(reconstruction_error, jsd_value)`:

1. Starts with score `100.0`.
2. If MSE exceeds `0.10`, subtracts
   `(reconstruction_error - 0.10) * 200`.
3. If JSD exceeds `0.30`, subtracts `(jsd_value - 0.30) * 100`.
4. Clips result to `[0.0, 100.0]`.
5. Rounds to two decimal places.

Dashboard status mapping:

| Trust Score | Status |
| --- | --- |
| `>= 50` | Healthy / Online |
| `30 <= score < 50` | Compromised |
| `< 30` | Critical |

Additional dashboard override:

If current feature values exactly match the device baseline, `dashboard.py`
forces `mse = 0.0` and `trust_score = 100.0` after updating metric histories.

Local sanity-check results:

| Check | Result |
| --- | --- |
| `calculate_jsd([0.4,0.5,0.3,0.6], same)` | `0.0` |
| `calculate_trust_score(0.02, 0.05)` | `100.0` |
| `calculate_trust_score(0.45, 0.65)` | `0.0` |

## 11. Dashboard Inference Data Flow

The dashboard inference pipeline in `dashboard.py` is:

```text
Slider values
  |
  v
current_features = np.array([pkt, iat, entropy, symmetry])
  |
  v
feature_seq = np.tile(current_features, (10, 1))[np.newaxis, :, :]
  |
  v
tensor_input = torch.tensor(feature_seq, dtype=torch.float32)
  |
  v
autoencoder.reconstruction_error(tensor_input) -> mse
autoencoder(tensor_input) -> reconstructed tensor
  |
  v
per-feature MSE = mean((tensor_input - output) ** 2, dim=1)
  |
  v
calculate_jsd(current_features, baseline) -> jsd
calculate_trust_score(mse, jsd) -> trust_score
  |
  v
status, charts, packet history, threat log, report trigger
```

Only the slider-derived normalized features go into the model. The random
packet stream shown in the table is display/simulation data and is not used as
model input.

Slider controls:

| Label | State key prefix | Range |
| --- | --- | --- |
| Packet Size (Norm) | `pkt` | `0.0` to `1.0` |
| Inter-Arrival Time (Norm) | `iat` | `0.0` to `1.0` |
| Entropy (Norm) | `ent` | `0.0` to `1.0` |
| Symmetry (Norm) | `sym` | `0.0` to `1.0` |

Synthetic packet stream fields:

| Column | Generated value |
| --- | --- |
| `Time` | Current local time as `HH:MM:SS` |
| `Pkt Size` | Random float from 64 to 1500 |
| `IAT` | Random float from 0.001 to 0.05 |
| `Entropy` | Random float from 3 to 7.5 |
| `Symmetry` | Random float from 0.4 to 0.9 |
| `Status` | `"Safe"` or `"Alert"` based on current trust status |

The table is capped to the 12 most recent rows.

## 12. Attack Simulation

File: `dashboard.py`

The attack simulation is manual and synthetic. It does not send packets or use
Scapy.

Trigger:

- Sidebar button: "Launch Attack"
- Function: `_launch_attack(dev_id, dev_baseline)`

Flow:

1. Displays a Streamlit status block.
2. Shows three staged messages:
   - Probing network interfaces.
   - Injecting malicious traffic packets.
   - Escalating privilege / overloading buffers.
3. Calls `_advance_attack(...)` three times.
4. Stores staged slider values into `st.session_state["attack_values"]`.
5. Stores target ID into `st.session_state["attack_trigger"]`.
6. Calls `st.rerun()`.
7. On the next render, `render_device_dashboard()` applies staged values to the
   per-device slider keys.

`_advance_attack(...)`:

- Reads the current attack step for the device.
- Computes a delta as `min(0.12 + step * 0.08 + random(0.0, 0.06), 0.40)`.
- For each feature:
  - If the baseline feature is below `0.5`, increases the current value.
  - Otherwise decreases the current value.
  - Clips to `[0.0, 1.0]`.
- Increments `attack_step[dev_id]` up to `5`.

The sidebar renders attack severity labels based on step:

| Step | Label |
| --- | --- |
| 1 | LOW |
| 2 | MODERATE |
| 3 | HIGH |
| 4 | SEVERE |
| 5 | CRITICAL |

## 13. Remediation Flow

File: `dashboard.py`

Trigger:

- Device is not safe.
- User clicks "Remediate Device".
- Function: `_run_remediation(dev_id, device_info)`

Flow:

1. Sets `st.session_state.remediation_locked = True`.
2. Records current timestamp and previous device status.
3. Appends a remediation log entry:
   - `Timestamp`
   - `Device ID`
   - `Device Name`
   - `Sector`
   - `Action Taken = "Quarantine Lifted & Params Reset"`
4. Inserts an audit log entry:
   - `device`
   - `timestamp`
   - `event = "Remediation Success"`
   - `previous_status`
5. Shows a three-step status sequence:
   - Resetting device parameters.
   - Flushing network buffers.
   - Re-synchronizing digital twin.
6. Sets the selected device health to `"Healthy"`.
7. Sets `remediation_reset` to the device ID.
8. Clears `threat_log`.
9. Unlocks remediation and reruns.
10. On the next render, `render_device_dashboard()` resets the four sliders to
    baseline values and resets attack step to zero.

This is a UI simulation only. It does not call external network control APIs,
firewall rules, device management services, or quarantine systems.

## 14. Authentication and Database

Files:

- `auth.py`
- `auth_page.py`
- `aegis_auth.db`

### Database

The auth database is SQLite. Default path:

```text
<project root>/aegis_auth.db
```

Override path:

```text
AEGIS_AUTH_DB_PATH
```

Actual schema from the current database:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

SQLite also contains the internal `sqlite_sequence` table because the users
table uses `AUTOINCREMENT`.

Current inspected database state:

| Table | Records |
| --- | --- |
| `users` | 7 |

No user emails or hashes are listed here because they are credential data.

### Password Hashing

`auth.py` uses:

1. UTF-8 encode password if needed.
2. SHA-256 digest of the password bytes.
3. `bcrypt.hashpw(digest, bcrypt.gensalt())`.
4. Store bcrypt hash string in SQLite.

Verification repeats SHA-256 prehashing and checks with `bcrypt.checkpw(...)`.

The SHA-256 prehash avoids bcrypt's 72-byte input truncation behavior.

### User Lifecycle

Public functions in `auth.py`:

| Function | Purpose |
| --- | --- |
| `_hash_password(password)` | Internal password hashing helper |
| `_verify_password(password, password_hash)` | Internal password verification helper |
| `_get_connection()` | Creates SQLite connection with row factory |
| `init_db()` | Creates `users` table if it does not exist |
| `create_user(email, password)` | Normalizes email, hashes password, inserts user |
| `has_users()` | Returns whether at least one user exists |
| `get_user(email)` | Returns user row as dict or `None` |
| `verify_user(email, password)` | Checks login credentials |

First admin bootstrap in `app.py`:

- If `has_users()` is false:
  - Reads `AEGIS_ADMIN_EMAIL`.
  - Reads `AEGIS_ADMIN_PASSWORD`.
  - Calls `create_user(...)` if both are set.

Registration behavior:

- The login page allows toggling into register mode.
- New users can be created from the UI.
- There is no authorization layer, invite check, email verification, rate
  limiting, password policy, account lockout, or admin role enforcement.

## 15. Forensic Reporting

File: `forensics.py`

Purpose:

- Build structured incident data.
- Enrich it with severity, attack pattern, top anomalies, and incident
  signature.
- Render a PDF report with ReportLab.
- Optionally send the PDF by SMTP with TLS.

### Data Model

`ForensicReportData` dataclass fields:

| Field | Meaning |
| --- | --- |
| `device_id` | Device identifier |
| `device_name` | Device display name |
| `sector` | Device sector |
| `timestamp` | Incident timestamp |
| `trust_score` | Current Trust Score |
| `reconstruction_error` | MSE anomaly score |
| `jsd_value` | Jensen-Shannon Divergence |
| `baseline_features` | Device baseline vector |
| `current_features` | Current feature vector |
| `packet_history` | Recent packet table records |
| `threat_log` | Recent threat log entries |
| `severity` | Derived severity |
| `attack_pattern` | Derived likely pattern |
| `top_anomalies` | Top feature deltas |
| `incident_signature` | SHA-256 incident fingerprint |

### Severity Logic

`_compute_severity(trust_score, jsd_value, mse)`:

| Condition | Severity |
| --- | --- |
| `trust_score < 25` or `jsd_value > 0.7` or `mse > 0.5` | CRITICAL |
| `trust_score < 40` or `jsd_value > 0.5` or `mse > 0.35` | HIGH |
| `trust_score < 60` or `jsd_value > 0.3` or `mse > 0.2` | MEDIUM |
| otherwise | LOW |

### Attack Pattern Heuristics

`_compute_attack_pattern(...)` uses baseline/current feature deltas:

| Heuristic | Pattern |
| --- | --- |
| Packet size delta > 0.35 and entropy delta > 0.25 | Data Exfiltration |
| IAT delta > 0.4 and symmetry delta > 0.3 | Botnet / Mass Scanning |
| Recent packet IAT has low standard deviation and max < 0.05 | Command and Control |
| Entropy delta > 0.25 | Suspicious Payloads / Obfuscation |
| none matched | Unknown |

### PDF Output

Main public function:

```python
generate_and_send_report(
    device_data: Dict[str, Any],
    output_dir: Optional[str] = None,
    recipient_email: Optional[str] = None,
    smtp_config: Optional[Dict[str, Any]] = None,
) -> str
```

Output directory resolution:

1. Explicit `output_dir`.
2. `FORENSICS_OUTPUT_DIR`.
3. `AEGIS_FORENSICS_OUT`.
4. `./reports`.

Filename pattern:

```text
forensic_report_<device_id>_<safe_device_name>_<UTC YYYYMMDD_HHMMSS>.pdf
```

Report sections:

- Incident header.
- Executive summary.
- Digital Twin analysis.
- Metrics table.
- Top anomaly contributing features.
- Behavioral timeline.
- Possible attack pattern.
- Risk assessment.
- Recommended remediation actions.
- Digital evidence snapshot.
- Incident signature.

### Email Sending

Public function:

```python
send_forensic_report(
    recipient_email: str,
    report_pdf_path: str,
    device_name: str,
    severity: str,
    trust_score: float,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
) -> bool
```

Environment variables:

| Variable | Purpose |
| --- | --- |
| `SMTP_SERVER` | SMTP host |
| `SMTP_PORT` | SMTP port, defaults to `587` |
| `SMTP_EMAIL` | SMTP username and sender |
| `SMTP_PASSWORD` | SMTP password |
| `AEGIS_ALERT_RECIPIENT` | Fallback recipient if one is not passed |

Dashboard trigger:

- In `dashboard.py`, if device is not safe and `trust_score < 30` and
  `st.session_state.user_email` exists, `_try_send_forensic_report(...)` calls
  `generate_and_send_report(...)` with `recipient_email` set to the logged-in
  user's email.
- A per-device cooldown prevents repeat sends for 10 minutes.
- If SMTP config is missing or sending fails, the dashboard catches the
  exception and shows a warning.

Important behavior:

When a recipient email is supplied but SMTP config is missing, the report PDF is
rendered before email sending raises an error. This means the file may still be
created even though the dashboard says sending failed.

## 16. APIs

### HTTP/REST APIs

There are no application-defined HTTP API endpoints, REST routes, GraphQL
schemas, FastAPI/Flask/Django servers, or webhook handlers in the repository.

Streamlit itself serves the browser application and manages its own internal
runtime protocol, but that is framework infrastructure, not a project API.

### Internal Python APIs

The project's reusable internal APIs are Python functions/classes:

| Module | API | Purpose |
| --- | --- | --- |
| `auth.py` | `init_db()` | Create auth schema |
| `auth.py` | `create_user(email, password)` | Register a user |
| `auth.py` | `has_users()` | Check whether DB has users |
| `auth.py` | `get_user(email)` | Fetch a user record |
| `auth.py` | `verify_user(email, password)` | Authenticate credentials |
| `auth_page.py` | `render_login_page()` | Render auth UI |
| `dashboard.py` | `render_device_dashboard(autoencoder)` | Render selected device dashboard |
| `engine.py` | `calculate_jsd(p, q)` | Compute distribution drift |
| `engine.py` | `calculate_trust_score(reconstruction_error, jsd_value)` | Compute 0-100 trust |
| `forensics.py` | `generate_and_send_report(...)` | Generate PDF and optionally email it |
| `forensics.py` | `send_forensic_report(...)` | Send an existing PDF through SMTP |
| `model.py` | `Encoder`, `Decoder`, `LSTMAutoencoder` | Model architecture |
| `ui.py` | `inject_css()` | Inject shared global CSS |
| `ui.py` | `glass_card(...)` | Styled Streamlit container context manager |
| `ui.py` | `section_header(...)` | Styled section header helper |

### External Service Interfaces

| Interface | Used by | Purpose |
| --- | --- | --- |
| SMTP with STARTTLS | `forensics.py` | Send PDF incident reports |
| CartoDB map tiles | Folium map in `app.py` | Render dark map background |
| Google Fonts CSS | `ui.py` | Load Inter and Source Code Pro fonts |

Scapy is imported in `app.py` (`from scapy.all import sniff`) but no active
code calls `sniff()` or ingests live packets.

## 17. Frontend/UI Implementation

Framework:

- Streamlit drives the UI.
- Plotly renders interactive charts.
- Folium and `streamlit-folium` render the map.
- Pandas Styler formats the packet stream table.
- Custom CSS is injected with `st.markdown(..., unsafe_allow_html=True)`.

Main UI surfaces:

| Surface | Implementation |
| --- | --- |
| Auth form | `auth_page.render_login_page()` |
| Fleet map | `app.render_fleet_page()` with `folium.Map`, `folium.Marker`, `st_folium` |
| Device sidebar | `dashboard._render_sidebar()` |
| Trust gauge | `dashboard._gauge_chart()` using `go.Indicator` |
| JSD sparkline | `dashboard._sparkline_chart()` using `go.Scatter` |
| Feature radar | `dashboard._radar_chart()` using `go.Scatterpolar` |
| Neural pulse chart | `dashboard._pulse_chart()` using two Plotly line traces |
| Packet table | `st.dataframe` over `st.session_state.packet_history` |
| Threat log | Custom HTML rows in Streamlit markdown |
| Math panel | Streamlit LaTeX and progress bar |
| Remediation/audit history | Fleet-page pandas tables |

Theme constants:

| Constant | Value |
| --- | --- |
| `NEON_GREEN` | `#00ff88` |
| `NEON_RED` | `#ff2d55` |
| `NEON_BLUE` | `#00cfff` |
| `NEON_CYAN` in `app.py` | `#00fff2` |
| `NEON_PINK` in `app.py` | `#ff007f` |

The visual style is a dark SOC/cyber dashboard with:

- Radial dark background.
- Subtle grid background.
- Glassmorphism containers.
- Neon borders and glow effects.
- Pulsing red states for compromised/critical devices.
- Monospace headings.

## 18. Backend and Data Processing

There is no standalone backend service. The backend responsibilities are handled
inside the Streamlit process:

| Responsibility | Implementation |
| --- | --- |
| Login credential storage | SQLite via `auth.py` |
| Password hashing | SHA-256 prehash plus bcrypt |
| Model inference | PyTorch in `dashboard.py` and `model.py` |
| Anomaly scoring | NumPy/SciPy in `engine.py` |
| Report generation | ReportLab in `forensics.py` |
| Email delivery | `smtplib.SMTP` in `forensics.py` |
| Runtime state | `st.session_state` |

There is no background job worker, task queue, async runtime, API controller,
database migration system, ORM, or production logging pipeline.

## 19. Storage and Generated Artifacts

### SQLite Auth Database

Path:

```text
aegis_auth.db
```

Purpose:

- Stores user email, bcrypt password hash, and creation timestamp.

Security note:

- The database currently exists in the repository root.
- `.gitignore` does not ignore `*.db`.
- Treat this file as sensitive because it contains credential hashes.

### Forensic Reports

Path:

```text
reports/
```

Current inventory:

| Device | PDF count |
| --- | --- |
| `DEV-001` | 4 |
| `DEV-002` | 2 |
| `DEV-003` | 38 |
| `DEV-006` | 1 |
| `DEV-007` | 2 |
| `DEV-008` | 1 |
| `DEV-010` | 16 |
| Total | 64 |

These are generated forensic incident PDFs. They are not used to run the app.

### Bytecode Cache

Path:

```text
__pycache__/
```

Contains generated `.pyc` files for Python 3.13 and 3.14. These are runtime
caches, not source files.

### Repomix Output

Path:

```text
repomix-output.xml
```

This is a generated packed representation of repository contents for AI/code
review tools. Its own header says it should be treated as read-only and that
changes should be made to original files, not the packed representation.

### PRD Document

Path:

```text
PRD doc.docx
```

The PRD describes the intended product concept. Some details differ from the
current code. For example, the PRD mentions Pydeck/MapGL, while the inspected
implementation uses Folium and `streamlit-folium`.

## 20. Dependency Inventory

### requirements.txt

The file lists unpinned dependencies:

```text
streamlit
pandas
numpy
plotly
matplotlib
pdfplumber
torch
torchvision
torchaudio
networkx
sympy
scipy
scikit-learn
shap
pydeck
python-dotenv
bcrypt
reportlab
folium
streamlit-folium
scapy
```

### Dependency Usage by Current Source

| Dependency | Used now? | Where/why |
| --- | --- | --- |
| `streamlit` | Yes | Main UI, widgets, state, charts, reruns |
| `pandas` | Yes | Packet history and report/audit tables |
| `numpy` | Yes | Feature arrays, tiling, clipping, JSD inputs |
| `plotly` | Yes | Gauge, sparkline, radar, pulse charts |
| `torch` | Yes | LSTM autoencoder model and inference |
| `scipy` | Yes | `scipy.stats.entropy` for JSD |
| `python-dotenv` | Yes | `load_dotenv()` in `app.py` |
| `bcrypt` | Yes | Password hashing and verification |
| `reportlab` | Yes | PDF report generation |
| `folium` | Yes | Fleet map |
| `streamlit-folium` | Yes | Embedding Folium map in Streamlit |
| `scapy` | Imported but unused | `sniff` imported in `app.py`, no active use |
| `matplotlib` | Not used by source | Listed only |
| `pdfplumber` | Not used by source | Listed only |
| `torchvision` | Not used by source | Listed only |
| `torchaudio` | Not used by source | Listed only |
| `networkx` | Not used by source | Listed only |
| `sympy` | Not used by source | Listed only |
| `scikit-learn` | Not used by source | Listed and checked by `check_setup.py` |
| `shap` | Not used by source | Listed and checked by `check_setup.py` |
| `pydeck` | Not used by source | Listed, PRD mentions map concept, current code uses Folium |

### Current Local Import Status

The inspected interpreter reported:

| Package/module | Status | Version if available |
| --- | --- | --- |
| `streamlit` | OK | `1.52.2` |
| `pandas` | OK | `2.3.3` |
| `numpy` | OK | `2.3.5` |
| `plotly` | OK | `6.5.0` |
| `matplotlib` | OK | `3.10.7` |
| `pdfplumber` | OK | `0.11.8` |
| `torch` | OK | `2.10.0+cpu` |
| `torchvision` | OK | `0.25.0+cpu` |
| `torchaudio` | OK | `2.10.0+cpu` |
| `networkx` | OK | `3.6.1` |
| `sympy` | OK | `1.14.0` |
| `scipy` | OK | `1.17.1` |
| `sklearn` | Missing | `ModuleNotFoundError` |
| `shap` | Missing | `ModuleNotFoundError` |
| `pydeck` | OK | `0.9.1` |
| `dotenv` | OK | version unknown |
| `bcrypt` | OK | `5.0.0` |
| `reportlab` | OK | `4.4.10` |
| `folium` | OK | `0.20.0` |
| `streamlit_folium` | Missing | `ModuleNotFoundError` |
| `scapy` | OK | `2.7.0` |

`check_setup.py` only checks a subset of dependencies:

- `streamlit`
- `pandas`
- `plotly`
- `torch`
- `sklearn`
- `scipy`
- `shap`

It does not check several currently required runtime modules such as
`streamlit_folium`, `folium`, `bcrypt`, `reportlab`, or `python-dotenv`.

### Python Version

Observed local command output:

```text
Python: 3.14.0
```

Project configuration expects Python 3.13:

- `pyrightconfig.json`: `"pythonVersion": "3.13"`
- `.vscode/settings.json`: `${workspaceFolder}/venv/Scripts/python.exe`
- `PROGRESS.md`: earlier notes mention Python 3.13.2

The repository also contains bytecode cache files for both Python 3.13 and
3.14.

## 21. Configuration and Environment Variables

Environment is loaded through `python-dotenv`:

```python
load_dotenv()
```

Recognized variables:

| Variable | Used by | Purpose |
| --- | --- | --- |
| `AEGIS_AUTH_DB_PATH` | `auth.py` | Override SQLite auth DB path |
| `AEGIS_ADMIN_EMAIL` | `app.py` | Seed first admin user if DB has no users |
| `AEGIS_ADMIN_PASSWORD` | `app.py` | Password for first admin seed |
| `SMTP_SERVER` | `forensics.py` | SMTP host |
| `SMTP_PORT` | `forensics.py` | SMTP port, defaults to `587` |
| `SMTP_EMAIL` | `forensics.py` | SMTP username/sender |
| `SMTP_PASSWORD` | `forensics.py` | SMTP password |
| `FORENSICS_OUTPUT_DIR` | `forensics.py` | Preferred report output directory |
| `AEGIS_FORENSICS_OUT` | `forensics.py` | Alternate report output directory |
| `AEGIS_ALERT_RECIPIENT` | `forensics.py` | Fallback report recipient |

`.gitignore` ignores:

```text
.env
.env.*
!.env.example
```

There is no `.env.example` file currently present in the inspected tree.

## 22. Development Tooling

### Pyright

File: `pyrightconfig.json`

Settings:

- `venvPath`: `.`
- `venv`: `venv`
- `pythonVersion`: `3.13`
- `typeCheckingMode`: `basic`
- `reportMissingImports`: `none`
- `reportMissingModuleSource`: `none`
- Included files:
  - `engine.py`
  - `model.py`
  - `check_setup.py`
- Excluded:
  - `venv`

Important limitation:

Pyright currently excludes or ignores several active modules:

- `app.py`
- `auth.py`
- `auth_page.py`
- `dashboard.py`
- `forensics.py`
- `registry.py`
- `ui.py`

This means static type checking does not cover most of the application.

### VS Code

File: `.vscode/settings.json`

It points VS Code at:

```text
${workspaceFolder}/venv/Scripts/python.exe
```

and configures Python analysis to use the local `venv`.

## 23. How to Run Locally

Recommended setup:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Optional first-admin bootstrap:

```powershell
$env:AEGIS_ADMIN_EMAIL = "admin@example.com"
$env:AEGIS_ADMIN_PASSWORD = "replace-with-a-strong-password"
streamlit run app.py
```

Run dependency checker:

```powershell
python -X utf8 check_setup.py
```

The `-X utf8` flag avoids Windows console encoding errors from emoji output in
`check_setup.py`.

Run model smoke test:

```powershell
python model.py
```

Run engine smoke test:

```powershell
python engine.py
```

Syntax compile check used during this analysis:

```powershell
python -m py_compile app.py auth.py auth_page.py dashboard.py engine.py forensics.py model.py registry.py ui.py check_setup.py
```

This compile check passed.

## 24. File-by-File Technical Reference

### app.py

Role:

- Main Streamlit entrypoint.
- Sets page configuration.
- Loads environment variables.
- Initializes auth database.
- Seeds a first user from env vars if no user exists.
- Injects CSS.
- Initializes session state.
- Applies auth guard.
- Caches the PyTorch model.
- Renders the fleet map.
- Routes to the selected page.

Main functions:

| Function | Purpose |
| --- | --- |
| `load_aegis_model()` | Instantiates `LSTMAutoencoder`, sets eval mode, cached by Streamlit |
| `render_fleet_page()` | Renders geospatial fleet overview and click navigation |

Key imports:

- `streamlit`
- `pandas`
- `torch`
- `folium`
- `streamlit_folium.st_folium`
- `dotenv.load_dotenv`
- local auth, dashboard, model, registry, and UI modules

Notable unused or duplicate imports/config:

- `plotly.graph_objects as go` is imported but charting is in `dashboard.py`.
- `time`, `datetime`, `threading`, `calculate_trust_score`,
  `calculate_jsd`, `add_script_run_ctx`, `get_script_run_ctx`, and Scapy
  `sniff` are imported but not actively used by current `app.py`.
- `LSTMAutoencoder` is imported twice.
- `PHONE_MAC`, `PHONE_BASELINE`, and phone-related session keys are unused.
- `IOT_REGISTRY` is imported from `registry.py` and then overwritten.

Critical current issues:

- Missing `streamlit_folium` in the inspected interpreter blocks import.
- Random local `IOT_REGISTRY` lacks `lat`/`lon` but `render_fleet_page()` needs
  them.
- The router calls `render_device_dashboard(autoencoder)`, but the model
  variable is named `model_engine`.

### dashboard.py

Role:

- Contains the active device dashboard.
- Calculates runtime model/scoring metrics.
- Renders all major visualizations.
- Manages attack simulation, remediation, report trigger, packet stream, and
  threat log.

Main functions:

| Function | Purpose |
| --- | --- |
| `_resolve_status(trust_score)` | Maps trust score to safe/critical/status color/classes |
| `_try_send_forensic_report(...)` | Builds report payload and calls forensic report generator |
| `_run_remediation(dev_id, device_info)` | Simulates remediation and logs it |
| `_gauge_chart(...)` | Builds Plotly trust gauge |
| `_sparkline_chart(...)` | Builds compact JSD trend |
| `_radar_chart(...)` | Builds baseline vs current feature radar |
| `_pulse_chart(...)` | Builds MSE/JSD trend chart |
| `render_device_dashboard(autoencoder)` | Main page renderer |
| `_render_sidebar(...)` | Sidebar controls and attack/remediation navigation |
| `_launch_attack(...)` | Simulated attack workflow |
| `_advance_attack(...)` | Mutates staged slider values |

Current behavior:

- Uses `registry.IOT_REGISTRY`, not the overwritten registry in `app.py`.
- Expects `packet_history` to be a pandas DataFrame when styling/rendering.
- Uses `time.sleep(1.0)` plus `st.rerun()` for live updates.
- Sends forensic reports only for trust below 30 and only if a user email is
  present.

### model.py

Role:

- Defines the LSTM autoencoder architecture.
- Exposes reconstruction error as an anomaly score.
- Includes a `__main__` smoke test.

Main classes:

| Class | Purpose |
| --- | --- |
| `Encoder` | LSTM encoder plus linear latent projection |
| `Decoder` | Linear expansion plus LSTM decoder and output projection |
| `LSTMAutoencoder` | Full model with `forward` and `reconstruction_error` |

Current limitation:

- No trained weights are loaded.
- No training pipeline exists in the repository.

### engine.py

Role:

- Implements statistical drift and scoring.
- Has no Streamlit dependency.
- Includes a `__main__` scenario test.

Main functions:

| Function | Purpose |
| --- | --- |
| `calculate_jsd(p, q)` | Jensen-Shannon Divergence in `[0, 1]` |
| `calculate_trust_score(reconstruction_error, jsd_value)` | Composite Trust Score in `[0, 100]` |

### registry.py

Role:

- Defines the canonical fixed fleet of 10 devices.
- Defines canonical session defaults.

Current limitation:

- Device data is hardcoded in Python.
- There is no loader from JSON, YAML, database, or service.

### auth.py

Role:

- Owns the auth DB connection and schema.
- Owns password hashing and verification.
- Provides user CRUD/read helpers needed by the login page.

Main functions:

| Function | Purpose |
| --- | --- |
| `init_db()` | Creates schema |
| `create_user(email, password)` | Creates a normalized user |
| `has_users()` | Checks whether any user exists |
| `get_user(email)` | Reads user by email |
| `verify_user(email, password)` | Validates credentials |

### auth_page.py

Role:

- Renders Streamlit auth UI.
- Coordinates login/register behavior with `auth.py`.

Main functions:

| Function | Purpose |
| --- | --- |
| `render_login_page()` | Shows form and stops app if unauthenticated |
| `_set_authenticated(email)` | Updates session state on successful auth |

### forensics.py

Role:

- Creates forensic incident reports.
- Renders PDFs.
- Sends report emails.

Main APIs:

| API | Purpose |
| --- | --- |
| `ForensicReportData` | Incident/report data container |
| `generate_and_send_report(...)` | Build data, render PDF, send if recipient exists |
| `send_forensic_report(...)` | Send report PDF through SMTP |

### ui.py

Role:

- Shared visual constants and CSS helpers.

Main APIs:

| API | Purpose |
| --- | --- |
| `NEON_GREEN`, `NEON_RED`, `NEON_BLUE` | Shared theme colors |
| `inject_css()` | Global CSS injection |
| `glass_card(...)` | Styled container context manager |
| `section_header(...)` | Consistent section heading |

### check_setup.py

Role:

- Verifies imports and prints installed versions for a subset of packages.

Current issue:

- On the inspected Windows console, running `python check_setup.py` failed with
  a Unicode encoding error while printing emoji.
- Running `python -X utf8 check_setup.py` worked and showed missing `sklearn`
  and `shap`.

## 25. Current Runtime Verification Results

Commands run during this analysis:

| Command | Result |
| --- | --- |
| `python -m py_compile ...` | Passed for all Python modules |
| `python -X utf8 check_setup.py` | Ran, but reported missing `sklearn` and `shap` |
| Full requirements import probe | Reported missing `sklearn`, `shap`, and `streamlit_folium` |
| Model parameter probe | `122,212` parameters |
| Engine sanity probe | JSD same vector `0.0`; nominal trust `100.0`; anomalous trust `0.0` |
| SQLite schema probe | Found `users` table and 7 user records |

Important: compile success only confirms syntax validity. It does not prove the
Streamlit app runs end to end, especially because current import/runtime issues
exist.

## 26. Known Issues and Technical Debt

High-impact runtime issues:

1. `streamlit_folium` is required by `app.py` but missing in the inspected
   interpreter.
2. `app.py` overwrites imported `registry.IOT_REGISTRY` with a random registry
   that has no `lat`/`lon`, causing the Folium fleet map to fail when it tries
   to read coordinates.
3. `app.py` creates `model_engine = load_aegis_model()` but routes with
   `render_device_dashboard(autoencoder)`. `autoencoder` is undefined.
4. `packet_history` is first initialized as a list in `app.py`, while
   `dashboard.py` expects a pandas DataFrame. The map-click flow replaces it
   with a DataFrame, but the state initialization remains inconsistent.

Model/scoring limitations:

5. The autoencoder is not trained and no checkpoint is loaded.
6. There is no model persistence, training data, validation data, threshold
   calibration, or reproducible ML experiment metadata.
7. Trust thresholds are hardcoded in `engine.py`.
8. `calculate_jsd()` does not guard against zero-sum input vectors.
9. Metric histories may receive the raw random-weight MSE before the exact
   baseline override forces the displayed score to 100.

Product/runtime limitations:

10. No real packet capture is active, despite the Scapy import.
11. No real IoT device integration exists.
12. No real quarantine/remediation integration exists.
13. Live scan uses `time.sleep(1.0)` plus `st.rerun()`, which is simple but not
    ideal for scalability or responsiveness.
14. Map tiles and fonts rely on external network access.
15. SMTP must be configured for email delivery.

Security/data concerns:

16. `aegis_auth.db` is present in the repository and contains password hashes.
17. `.gitignore` does not ignore `*.db`, `reports/`, or `__pycache__/`.
18. There is no account role model, authorization layer, password policy, rate
    limiting, session expiry policy, CSRF design, or audit persistence for auth
    actions.
19. User registration appears available from the login UI without invite/admin
    approval.

Dependency/tooling issues:

20. `requirements.txt` is unpinned, so installs are not reproducible.
21. Several listed dependencies are unused by current source.
22. `check_setup.py` does not check all runtime-required modules.
23. `check_setup.py` can fail on Windows console encoding unless UTF-8 mode is
    enabled.
24. Pyright only includes three files and misses most of the app.
25. Existing root-level docs do not fully match current implementation.

Code hygiene issues:

26. Several imports in `app.py` are unused after refactoring.
27. `LSTMAutoencoder` is imported twice in `app.py`.
28. Phone-related constants/session keys appear to be legacy code.
29. The codebase has no automated unit tests, integration tests, or CI config.

## 27. Recommended Fix Order

For future maintainers, the most valuable stabilization order is:

1. Fix immediate app blockers:
   - Install or verify `streamlit-folium`.
   - Remove the random `IOT_REGISTRY` override in `app.py`.
   - Change `render_device_dashboard(autoencoder)` to
     `render_device_dashboard(model_engine)`.
   - Normalize `packet_history` initialization to a DataFrame.
2. Clean dependency and environment handling:
   - Pin dependency versions.
   - Update `check_setup.py` to check all runtime dependencies.
   - Add `.env.example`.
   - Ignore or remove local DB/report/cache artifacts if they are not meant to
     be source-controlled.
3. Add minimal tests:
   - Unit tests for `engine.calculate_jsd`.
   - Unit tests for `engine.calculate_trust_score`.
   - Unit tests for auth hashing/verification against a temp DB.
   - Forensics PDF smoke test to a temp directory without SMTP.
4. Decide ML scope:
   - If demo only, document random model behavior clearly in-app.
   - If real detection is required, add data ingestion, training, checkpoint
     loading, validation metrics, and calibrated thresholds.
5. Decide production architecture:
   - Keep Streamlit single-process for demos.
   - Split API/backend/storage only if real telemetry, multi-user operations,
     or production deployment are required.

## 28. Report Artifact Inventory

Current generated reports in `reports/`:

```text
forensic_report_DEV-001_AEGIS-PUMP-01_20260313_103454.pdf
forensic_report_DEV-001_AEGIS-PUMP-01_20260313_105100.pdf
forensic_report_DEV-001_AEGIS-PUMP-01_20260313_131300.pdf
forensic_report_DEV-001_AEGIS-PUMP-01_20260313_134551.pdf
forensic_report_DEV-002_Assembly_Arm_20260313_100434.pdf
forensic_report_DEV-002_Assembly_Arm_20260313_104202.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112553.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112555.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112556.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112557.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112558.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112559.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112601.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112602.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112603.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112605.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112606.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112607.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112608.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112610.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112611.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112612.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112613.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112615.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112616.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112617.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112619.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112620.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112621.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112622.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112624.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112625.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112626.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112628.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112629.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112630.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112631.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112632.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112633.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112641.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112655.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112656.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_112710.pdf
forensic_report_DEV-003_Grid_Node_0X_20260313_133507.pdf
forensic_report_DEV-006_Security_Cam_1_20260313_135446.pdf
forensic_report_DEV-007_Security_Cam_2_20260313_124356.pdf
forensic_report_DEV-007_Security_Cam_2_20260313_133739.pdf
forensic_report_DEV-008_Coolant_Pump_20260313_133848.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124143.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124144.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124146.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124147.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124148.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124150.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124151.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124152.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124154.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124155.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124156.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124158.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124159.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124201.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_124202.pdf
forensic_report_DEV-010_Main_Grid_Relay_20260313_135333.pdf
```

## 29. Glossary

| Term | Meaning in this project |
| --- | --- |
| Digital Twin | A software model of a device's normal traffic behavior |
| LSTM | Long Short-Term Memory neural network layer for sequence modeling |
| Autoencoder | Model trained to reconstruct input; reconstruction error acts as anomaly score |
| MSE | Mean Squared Error between model input and reconstruction |
| JSD | Jensen-Shannon Divergence between current feature vector and baseline vector |
| Trust Score | 0-100 score derived from MSE and JSD penalties |
| Baseline | Four-feature "normal" vector for a device |
| Packet Size | Normalized traffic feature used by the model |
| IAT | Inter-Arrival Time, normalized traffic timing feature |
| Payload Entropy | Normalized entropy feature representing payload randomness |
| Flow Symmetry | Normalized traffic balance/symmetry feature |
| Remediation | Simulated reset/quarantine-lift workflow in the UI |
| Forensic report | Generated PDF incident report with metrics and suggested actions |
| Streamlit session state | In-memory per-session key-value store used for app runtime state |
