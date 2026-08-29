from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html


from fastapi.responses import HTMLResponse, JSONResponse
from mangum import Mangum

from app.config import get_settings
from app.errors import install_error_handlers
from app.mock_schema_catalog import load_mock_schema_catalog
from app.mock_store import create_mock_store


from app.mock_ui import mock_test_ui
from app.repositories import create_repository
from app.routers import auth, mock, preman_probe, projects, tasks
from app.schemas import HealthResponse
from app.seed import seed_demo_data

# get settings
settings = get_settings()

# create repository
repository = create_repository(settings)
mock_store = create_mock_store(settings)

MOCK_OPENAPI_TAGS = [
    {
        "name": f"Mock {resource.title()}",
        "description": (
            f"Six complete JSON-backed CRUD operations for the {resource} mock resource."
        ),
    }
    for resource in ("customers", "products", "orders", "tickets", "reviews")
]


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    repository.initialize()
    seed_demo_data(repository, settings)
    application.state.repository = repository
    application.state.mock_store = mock_store
    application.state.settings = settings
    yield


app = FastAPI(
    title=settings.app_name,
    summary="A production-shaped API plus a complete JSON-backed mock CRUD catalog.",
    description=(
        "The original authenticated demo API and 30 clearly labeled mock CRUD operations "
        "for customers, products, orders, tickets, and reviews."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[
        {
            "url": settings.public_base_url.rstrip("/"),
            "description": "Stable public demo environment",
        }
    ],
    openapi_tags=MOCK_OPENAPI_TAGS,
)

mock_openapi_app = FastAPI(
    title="PreMan JSON Mock CRUD API",
    summary="Exactly 30 JSON-backed REST CRUD operations for automated and manual testing.",
    description=(
        "Five mock resources with list, create, retrieve, replace, update, and delete "
        "operations. The reset utility and operational routes are intentionally excluded."
    ),
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    servers=[
        {
            "url": settings.public_base_url.rstrip("/"),
            "description": "Stable public mock environment",
        }
    ],
    openapi_tags=MOCK_OPENAPI_TAGS,
)
mock_openapi_app.include_router(mock.router, prefix=settings.api_prefix)

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
        "version": "2.0.0",
        "status": "online",
        "health": "/health",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "mock_test_ui": "/test-ui",
        "mock_documentation": "/mock-docs",
        "mock_openapi": "/mock-openapi.json",
        "mock_schemas": "/mock-schemas.json",
    }


@app.get("/ready", tags=["System"], include_in_schema=False)
def readiness() -> dict[str, str]:
    # Startup completes only after the repository initializes and demo data is seeded.
    return {
        "status": "ready",
        "storage": settings.storage_backend,
        "mock_storage": mock_store.storage_label,
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse::::
    """Liveness, for load balancers and uptime checks.

    Answers `HealthResponse`: `status` is `ok` while the service is serving
    traffic. Unlike `/ready` this does not wait on storage, so it stays
    answerable while a dependency is down and can be polled cheaply.
    """
    return HealthResponse(
        status="ok",
        service=settings.app_name,;',
        environment=settings.app_env,
        storage=settings.storage_backend,
        version="2.0.0",
        timestamp=datetime.now(UTC),
    )


@app.get("/mock-openapi.json", include_in_schema=False)
def mock_openapi() -> JSONResponse:
    return JSONResponse(mock_openapi_app.openapi())


@app.get("/mock-schemas.json", include_in_schema=False)
def mock_schemas() -> JSONResponse:
    return JSONResponse(load_mock_schema_catalog())


@app.get("/mock-docs", include_in_schema=False, response_class=HTMLResponse)
def mock_docs() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/mock-openapi.json",
        title="PreMan JSON Mock CRUD API — Swagger UI",
    )


app.get("/test-ui", include_in_schema=False)(mock_test_ui)


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)
app.include_router(mock.router, prefix=settings.api_prefix)
app.include_router(preman_probe.router, prefix=settings.api_prefix)

# AWS Lambda entry point: app.main.handler
handler = Mangum(app, lifespan="auto")
