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
│   └── aegis-lstm-autoencoder/
│       └── v1/                  # exported model artifacts and checkpoints
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

The project uses the Aegis LSTM autoencoder as its digital twin model.

### Model location

The model artifacts live under:

- `model-store/aegis-lstm-autoencoder/v1/`

This directory is reserved for release-ready model checkpoints, metadata, and any saved inference weights.

### What `model-store/aegis-lstm-autoencoder` is

It represents the trained LSTM autoencoder model used to score whether device activity deviates from normal behavior. In other words, it is the model package that encodes the learned baseline for device telemetry.

### How to train or replace a model

1. Prepare training data in the expected feature format used by the current app.
2. Train your LSTM autoencoder in the backend or a dedicated ML job.
3. Save the trained weights into `model-store/aegis-lstm-autoencoder/v1/`.
4. Update the loading path in the backend model service so the new checkpoint is referenced.
5. Restart the backend service.

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

- Keep frontend logic in `app/web` and backend logic in `services/backend/api`.
- Avoid creating ad hoc root-level scripts and services.
- Keep model artifacts in `model-store/` rather than in the application code directory.
- Update this README and the technical source of truth whenever the architecture changes.
