"""
app/server.py — FastAPI application factory.

Call ``create_app()`` to get a configured ``FastAPI`` instance.
This keeps the app object away from the module-level scope so it can be
imported by tests without side effects.

Usage (production)::

    uvicorn app.server:app --host 0.0.0.0 --port 8000

Usage (dev with reload)::

    uvicorn app.server:app --reload
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import shutdown_posture_service
from app.api.v1.router import api_router
from app.config import DATA_DIR, SESSION_DIR
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    # ── Ensure data directories exist ─────────────────────────────────
    os.makedirs(SESSION_DIR, exist_ok=True)

    # ── Application instance ──────────────────────────────────────────
    app = FastAPI(
        title       = "PostureCoach API",
        description = (
            "Real-time posture analysis via MediaPipe.  "
            "Stream webcam frames over WebSocket and receive per-frame "
            "posture classification, alert state, and calibration progress."
        ),
        version     = "1.0.0",
        docs_url    = "/docs",
        redoc_url   = "/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────
    # Restrict origins in production via the CORS_ORIGINS env var:
    #   CORS_ORIGINS="https://app.example.com,https://staging.example.com"
    app.add_middleware(
        CORSMiddleware,
        allow_origins     = settings.cors_origin_list,
        allow_credentials = True,
        allow_methods     = ["*"],
        allow_headers     = ["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # ── Lifecycle ─────────────────────────────────────────────────────
    @app.on_event("startup")
    async def _startup() -> None:
        if False:
            Base.metadata.create_all(bind=engine)
        logger.info("PostureCoach API starting up.")

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        logger.info("PostureCoach API shutting down — flushing session log.")
        shutdown_posture_service()

    return app


# Module-level app object so uvicorn can find it with ``app.server:app``
app = create_app()
