"""
api/deps.py — FastAPI dependency providers.

Import these with ``Depends()`` in route functions.  Each provider yields
a singleton or per-request object and handles cleanup automatically.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import get_token_subject
from app.db.session import get_db
from app.models import User
from app.repositories import UserRepository

from app.services.posture_service import PostureService
from app.services.session_service import SessionService

bearer_scheme = HTTPBearer(auto_error=False)


# ── Singleton PostureService ───────────────────────────────────────────────
# One PostureService lives for the lifetime of the process.  It owns the
# MediaPipe model, calibration state, alert timers, and the open CSV file.
# It is created lazily on the first request that needs it.

_posture_service: PostureService | None = None


def get_posture_service() -> PostureService:
    """Return the process-wide PostureService, creating it if necessary."""
    global _posture_service
    if _posture_service is None:
        _posture_service = PostureService()
    return _posture_service


def shutdown_posture_service() -> None:
    """Call during application shutdown to flush CSV and release resources."""
    global _posture_service
    if _posture_service is not None:
        _posture_service.close()
        _posture_service = None


# ── SessionService (stateless, cheap to construct) ────────────────────────

def get_session_service() -> SessionService:
    return SessionService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    user_id = get_token_subject(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token.")
    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


# ── Helpers ────────────────────────────────────────────────────────────────

def require_calibration(
    svc: PostureService = None,   # injected at call site
) -> PostureService:
    """
    Raise 409 if the service is not yet calibrated.

    Usage in a route::

        svc = Depends(get_posture_service)
        _   = require_calibration(svc)
    """
    if svc is None:
        svc = get_posture_service()
    if not svc._calibration.is_calibrated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Posture service is not calibrated yet. "
                   "POST /api/v1/calibration/start first.",
        )
    return svc
