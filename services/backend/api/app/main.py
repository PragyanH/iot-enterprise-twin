import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth, fleet, health, incidents, intelligence, trust
from app.core.runtime import trust_service

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000",
).split(",")

@asynccontextmanager
async def lifespan(_: FastAPI):
    async def update_mocks() -> None:
        while True:
            trust_service.tick_mock_devices()
            trust_service.refresh_staleness()
            await asyncio.sleep(1.0)

    task = asyncio.create_task(update_mocks())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Aegis-Twin API",
    version="1.0.0",
    description="API for the Aegis-Twin fleet analytics and digital twin platform.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
app.include_router(trust.router, prefix="/api/v1", tags=["trust"])
app.include_router(intelligence.router, prefix="/api/v1", tags=["intelligence"])
app.include_router(incidents.router, prefix="/api/v1", tags=["incidents"])


@app.get("/", tags=["meta"], summary="Root status")
def root() -> dict[str, str]:
    return {"service": "aegis-twin-api", "status": "ok"}
