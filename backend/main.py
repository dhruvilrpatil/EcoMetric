"""
EcoMetric FastAPI Application — main.py
Phase 0 scaffold with full middleware, CORS, health endpoint, and router registration.
All computation endpoints, inventory, and export endpoints are wired in later phases.
"""

from __future__ import annotations

import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Structured logging setup ──────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger(__name__)

# ── App lifecycle ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("EcoMetric API starting up", environment=os.getenv("ENVIRONMENT", "development"))
    yield
    logger.info("EcoMetric API shutting down")

# ── FastAPI application ────────────────────────────────────────────────
app = FastAPI(
    title="EcoMetric API",
    description=(
        "Enterprise EPD & Life Cycle Assessment automation platform. "
        "Implements EN 15804+A2, ISO 14025, ISO 14040/14044."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS middleware ────────────────────────────────────────────────────
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# ── Global exception handler — never expose internal errors to client ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    print(f"DEBUG EXCEPTION: {repr(exc)}", flush=True)
    if isinstance(exc, StarletteHTTPException):
        # Let FastAPI handle HTTP exceptions normally (CORS works out of the box for them)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    try:
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
    except:
        pass
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal error: {repr(exc)}",
            "code": "INTERNAL_ERROR",
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ── Health check ──────────────────────────────────────────────────────
@app.get("/health", tags=["system"], summary="Health check")
async def health_check():
    """Returns 200 if the API is running. Used by Docker healthchecks."""
    return {"status": "ok", "version": "1.0.0"}

# ── API v1 Router — will be populated in Phases 2–6 ──────────────────
from fastapi import APIRouter

api_v1 = APIRouter(prefix="/api/v1")

# Placeholder endpoints — actual implementations in later phases
@api_v1.get("/ping", tags=["system"])
async def ping():
    return {"message": "pong"}

from api.lci_search import router as lci_router
from api.calculation import router as calc_router
from api.export import router as export_router
from api.projects import router as projects_router
from api.nlp import router as nlp_router
from api.transportation import router as transportation_router
from api.verifier import router as verifier_router

api_v1.include_router(lci_router)
# calc_router routes (/projects/{id}/calculate, /projects/{id}/jobs/{id}) are
# included separately so they don't conflict with projects_router CRUD routes.
api_v1.include_router(calc_router)
api_v1.include_router(export_router)
api_v1.include_router(projects_router)
api_v1.include_router(nlp_router)
api_v1.include_router(transportation_router)
api_v1.include_router(verifier_router)

@api_v1.get("/epd/reference-matrix", tags=["Calculation"])
async def get_reference_matrix(methodology: Optional[str] = "EN_15804_A2"):
    """Returns verified Carrier EPD11017 reference matrix (Tables 18-22)."""
    from engine.lcia_matrix import get_epd11017_reference_matrix
    return get_epd11017_reference_matrix(methodology or "EN_15804_A2").model_dump()

app.include_router(api_v1)

