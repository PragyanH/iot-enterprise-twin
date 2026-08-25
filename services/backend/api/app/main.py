import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth, fleet, health

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000",
).split(",")

app = FastAPI(
    title="Aegis-Twin API",
    version="1.0.0",
    description="API for the Aegis-Twin fleet analytics and digital twin platform.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(fleet.router, prefix="/api/v1/fleet", tags=["fleet"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/", tags=["meta"], summary="Root status")
def root() -> dict[str, str]:
    return {"service": "aegis-twin-api", "status": "ok"}
