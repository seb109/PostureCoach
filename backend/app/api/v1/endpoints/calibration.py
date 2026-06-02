"""
api/v1/endpoints/calibration.py — Calibration management routes.

POST /calibration/start   — begin (or restart) a quick-cal sequence
GET  /calibration/status  — read current calibration state
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_posture_service
from app.api.schemas import CalibrationStatusResponse, RecalibrateResponse
from app.posture.calibration import CalPhase
from app.services.posture_service import PostureService

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.get(
    "/status",
    response_model=CalibrationStatusResponse,
    summary="Get calibration status",
)
def get_calibration_status(
    svc: PostureService = Depends(get_posture_service),
) -> CalibrationStatusResponse:
    """
    Returns whether the service is calibrated and, if so, the stored
    baseline distance and angle values.
    """
    return CalibrationStatusResponse(
        is_calibrated     = svc._calibration.is_calibrated,
        baseline_distance = svc._calibration.baseline_distance,
        baseline_angle    = svc._calibration.baseline_angle,
    )


@router.post(
    "/start",
    response_model=RecalibrateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start (or restart) calibration",
)
def start_calibration(
    svc: PostureService = Depends(get_posture_service),
) -> RecalibrateResponse:
    """
    Triggers a fresh quick-calibration sequence.  The client should then
    stream frames to the WebSocket endpoint; the calibration phase reported
    in each ``FrameAnalysisResponse`` will progress from ``WARMUP`` →
    ``COLLECT`` → ``DONE``.
    """
    svc.start_recalibration()
    return RecalibrateResponse(
        message="Calibration sequence started. Stream frames via WebSocket."
    )
