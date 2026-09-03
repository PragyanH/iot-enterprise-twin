# Aegis-Twin

Aegis-Twin is an AI-driven cybersecurity digital twin platform for enterprise and industrial IoT fleets. The project now uses a split architecture:

- Frontend: Next.js + Tailwind in `app/web`
- Backend: FastAPI service in `services/backend/api`
- Model artifacts: `model-store/`
- Infrastructure: `infra/`
- Automation scripts: `scripts/`

## Architecture overview

```text
Browser
  |
  v
Next.js frontend (localhost:3000)
  |
  | /api/* requests proxied through Next.js middleware
  v
FastAPI backend (localhost:8000)
  |
  +--> Fleet API routes
  +--> Health API routes
  +--> Auth API routes
  +--> Model and analytics services
```

## Project structure

```text
.
├── apps/
│   └── web/                     # Next.js frontend
├── services/
│   └── backend/
│       └── api/                 # FastAPI backend service
├── model-store/
│   ├── aegis-hybrid-trust/
│   │   └── v1/                  # active hybrid model package and baselines
│   └── aegis-lstm-autoencoder/  # legacy placeholder retained for reference
├── infra/
│   └── docker/                  # reusable Docker support files
├── scripts/
│   └── README.md                # explains intended automation scripts
├── data/
│   ├── reports/
│   └── uploads/
├── reports/
├── doc/
│   └── TECHNICAL_SOURCE_OF_TRUTH.md
├── docker-compose.yml
├── .gitignore
├── README.md
└── .env.example (optional)
```

## Local development

### 1) Install dependencies

Frontend:

```bash
cd app/web
npm install
```

Backend:

```bash
cd services/backend/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Start the backend

```bash
cd services/backend/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Start the frontend

```bash
cd app/web
npm run dev
```

Then open:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Backend health: http://localhost:8000/api/v1/health

### Windows Raspberry Pi telemetry

The finals live sensor is Npcap + TShark. After installing Wireshark/Npcap,
list interfaces and start the Pi-facing capture from the repository root:

```powershell
python scripts/tshark_live.py --list-interfaces
python scripts/tshark_live.py --interface 4 --target-ip 192.168.56.20
```

Use `doc/HARDWARE_DEMO_RUNBOOK.md` for recording, attack-controller and
physical acceptance steps. Zeek remains an alternate Linux sensor.

## Docker

From the project root:

```bash
docker compose up --build
```

Then:

- Frontend: http://localhost:3000
- API: http://localhost:8000

## API documentation

The backend uses OpenAPI/Swagger automatically via FastAPI.

Open these endpoints in a browser:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

The main routes include:

- GET `/api/v1/health`
- GET `/api/v1/fleet`
- POST `/api/v1/auth/login`

## Changing the color palette

The palette is defined in one place in the frontend:

- `app/web/src/app/globals.css`

Edit the CSS variables:

```css
:root {
  --color-primary: #4ecdc4;
  --color-secondary: #2b6cff;
  --color-accent: #f4d35e;
  --color-success: #35d399;
  --color-danger: #ff5f7a;
  --color-panel: #111827;
  --color-surface: #0f172a;
}
```

These variables are consumed by Tailwind classes defined in `tailwind.config.ts`.

## Model lifecycle and training

The active model is the **Aegis Hybrid Temporal Trust Engine**. It combines a
64-unit LSTM-VAE, temporal attention, a 16-dimensional latent space, XGBoost,
per-feature Jensen-Shannon divergence, deterministic Zeek rules, and a stable
trust-state composer.

### Model location

The model artifacts live under:

- `model-store/aegis-hybrid-trust/v1/`

This directory is reserved for release-ready model checkpoints, metadata, and any saved inference weights.

### Runtime trust API

The FastAPI backend exposes:

- `POST /api/v1/telemetry/windows`
- `GET /api/v1/devices/{device_id}/state`
- `GET /api/v1/events/trust` (server-sent events)
- `POST /api/v1/devices/{device_id}/remediate`
- `POST /api/v1/devices/{device_id}/simulate-attack`
- `POST /api/v1/demo/replay/pi_syn`
- `GET /api/v1/incidents` and incident detail/timeline/report routes
- `GET /api/v1/system/capabilities`

Both real Pi telemetry and mock telemetry use the same normalized window API.
The existing frontend design is unchanged and now receives live fleet trust
updates through SSE.
Step 3 persists detection-time forensic snapshots in SQLite, produces idempotent
HTML reports, exposes structured remediation phases, verifies three consecutive
clean windows before closure, and applies wall-clock staleness only to observed
live-hardware telemetry.

### How to train or replace a model

1. Capture session-labeled telemetry JSONL or use `--synthetic-demo`.
2. Run `python scripts/train_hybrid_models.py --input <sessions.jsonl>`.
3. Confirm that the generated `metrics.json` contains real held-out metrics.
4. Run `python scripts/run_demo_acceptance.py --loops 20`.
5. Restart the backend to load the frozen PyTorch and XGBoost artifacts.

When learned artifacts are absent, the backend explicitly reports calibrated
fallback model backends and retains reliable demo behavior; it never reports
untrained values as learned accuracy.

The repo is intentionally structured so model weights and metadata are separated from app code and API logic.

## Why `scripts` is empty

`scripts/` is reserved for operational automation such as:

- model training jobs
- data export/import scripts
- validation checks
- environment bootstrapping
- ad hoc maintenance tasks

It is empty right now because the project is still in the migration phase and the automation layer has not yet been populated. This is a conventional place for reusable project maintenance commands.

## Why `infra/docker` is empty

`infra/docker/` is meant to hold reusable Docker support files, such as:

- custom Dockerfiles
- runtime configuration templates
- healthcheck scripts
- environment manifests
- service-specific container config

At the moment it is empty because the project-level Docker orchestration is centralized in the root `docker-compose.yml` and no service-specific Docker files have been added yet.

## Middleware for frontend/backend separation

The Next.js middleware at `app/web/src/middleware.ts` handles API calls from the browser and proxies them to the backend:

```ts
if (pathname.startsWith("/api/")) {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const url = new URL(pathname.replace(/^\/api/, ""), backendUrl);
  return NextResponse.rewrite(url);
}
```

This keeps the frontend and backend on different localhosts without CORS issues.

## Swagger + OpenAPI

FastAPI automatically exposes:

- `/docs`
- `/redoc`
- `/openapi.json`

The API metadata is declared in `services/backend/api/app/main.py`, and each route has a summary/description for Swagger documentation.

## Docker Compose failure and fix

The original startup failed because the app was structured around the wrong backend path and missing runtime environment wiring.

The main issues were:

1. The backend build context was not aligned with the current directory layout.
2. The frontend needed a backend URL it could use in the browser.
3. The Next.js middleware was not present yet, so browser `/api/*` calls were not proxied.
4. The backend needed CORS enabled for the browser to talk to a different localhost.

These have been corrected in the final configuration.

## Example commands

Check the API:

```bash
curl http://localhost:8000/api/v1/health
```

Check the frontend:

```bash
curl http://localhost:3000
```

## Notes for contributors

For Raspberry Pi, Zeek, attack-controller, and replay setup, see
[`doc/HARDWARE_DEMO_RUNBOOK.md`](doc/HARDWARE_DEMO_RUNBOOK.md).

- Keep frontend logic in `app/web` and backend logic in `services/backend/api`.
- Avoid creating ad hoc root-level scripts and services.
- Keep model artifacts in `model-store/` rather than in the application code directory.
- Update this README and the technical source of truth whenever the architecture changes.

## Local enterprise workflow setup

Step 3.5 adds SQLite email/password authentication, role-scoped incident assignment, append-only investigation notes, optional SMTP notification, and deterministic HTML/PDF forensic reports. It does not change the frontend design or the hardware/detection pipeline.

Install backend dependencies and seed local demo users from environment-only passwords:

```powershell
services\backend\api\.venv\Scripts\python.exe -m pip install -r services\backend\api\requirements.txt
$env:AEGIS_DEMO_ADMIN_PASSWORD="choose-a-demo-secret"
$env:AEGIS_DEMO_OWNER_PASSWORD="choose-a-different-secret"
$env:AEGIS_DEMO_VENDOR_PASSWORD="choose-a-third-secret"
services\backend\api\.venv\Scripts\python.exe scripts\seed_demo_users.py
```

SMTP remains safely disabled with `AEGIS_SMTP_ENABLED=false`. For real delivery, set the host, port, username, password, from-address, and TLS values documented in `.env.example` before starting FastAPI. Assignment and all cyber lifecycle functions continue if SMTP is offline or rejects delivery.
