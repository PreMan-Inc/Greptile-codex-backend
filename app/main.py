from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.config import get_settings
from app.errors import install_error_handlers
from app.repositories import create_repository
from app.routers import auth, projects, tasks
from app.schemas import HealthResponse
from app.seed import seed_demo_data

settings = get_settings()
repository = create_repository(settings)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    repository.initialize()
    seed_demo_data(repository, settings)
    application.state.repository = repository
    application.state.settings = settings
    yield


app = FastAPI(
    title=settings.app_name,
    summary="A production-shaped API that PreMan can discover and test on every push.",
    description=(
        "A deterministic hackathon backend with authentication, projects, tasks, "
        "OpenAPI documentation, and stable demo data."
    ),
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.allowed_origins != ["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


install_error_handlers(app)


@app.get("/", tags=["System"], include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": "1.1.0",
        "status": "online",
        "health": "/health",
        "documentation": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/ready", tags=["System"], include_in_schema=False)
def readiness() -> dict[str, str]:
    # Startup completes only after the repository initializes and demo data is seeded.
    return {"status": "ready", "storage": settings.storage_backend}


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        storage=settings.storage_backend,
        version="1.1.0",
        timestamp=datetime.now(UTC),
    )


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)

# AWS Lambda entry point: app.main.handler
handler = Mangum(app, lifespan="auto")
