"""
api/v1/router.py — Mounts all v1 endpoint routers onto a single APIRouter.

Import ``api_router`` in the application factory and include it with the
``/api/v1`` prefix.
"""
from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.calibration import router as calibration_router
from app.api.v1.endpoints.health      import router as health_router
from app.api.v1.endpoints.posture import router as posture_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.sessions import router as legacy_sessions_router
from app.api.v1.endpoints.session_db import router as session_db_router
from app.api.v1.endpoints.stream      import router as stream_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(calibration_router)
api_router.include_router(users_router)
api_router.include_router(session_db_router)
api_router.include_router(posture_router)
api_router.include_router(reports_router)
api_router.include_router(legacy_sessions_router, prefix="/legacy")
api_router.include_router(stream_router)
