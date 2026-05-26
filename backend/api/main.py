from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from config import get_settings
from services.database import init_db, close_db
from services.logging_config import setup_logging
from middleware import (
    RequestTracingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    global_exception_handler,
)
from api import api_router

settings = get_settings()

# Setup logging
setup_logging(
    level="DEBUG" if settings.debug else "INFO",
    json_format=not settings.debug,
)
logger = logging.getLogger("omicsflow")

_start_time = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OmicsFlow starting up...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("OmicsFlow shutting down...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    description="BioSkills Based Bioinformatics Analysis Platform API",
    version="0.2.0",
    lifespan=lifespan,
)

# Exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_rpm)
app.add_middleware(RequestTracingMiddleware)

# CORS - restrict in production
if settings.debug:
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] if settings.cors_origins else ["http://localhost:3000"]
    if not cors_origins:
        cors_origins = ["http://localhost:3000"]
    logger.info(f"CORS origins (production): {cors_origins}")

# Security: warn if default secret key
if settings.secret_key in ("change-me", "your-secret-key", ""):
    logger.warning("⚠️  SECRET_KEY is using default value! Change it in production!")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Production mode warning: if cors_origins is non-empty and doesn't contain "*"
if cors_origins and "*" not in cors_origins:
    logger.warning(
        f"🔒 Production mode: CORS restricted to {cors_origins}. "
        "Ensure all required origins are included in CORS_ORIGINS env var."
    )

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    from services.task_queue import _tasks as active_tasks
    from services.websocket import ws_manager

    uptime = (datetime.now(timezone.utc) - _start_time).total_seconds()

    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "0.2.0",
        "uptime_seconds": int(uptime),
        "active_tasks": len(active_tasks),
        "ws_connections": ws_manager.active_connections,
        "debug": settings.debug,
    }


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
    }
