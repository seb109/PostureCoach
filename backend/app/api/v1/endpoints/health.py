"""
api/v1/endpoints/health.py — Liveness / readiness probe.
"""
from fastapi import APIRouter
from app.api.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["health"],
)
def health_check() -> HealthResponse:
    """Returns ``{"status": "ok"}`` — used by load-balancers and CI smoke tests."""
    return HealthResponse()
