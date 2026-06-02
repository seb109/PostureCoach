"""
api/v1/endpoints/sessions.py — Session history routes.

GET  /sessions                      — list all recorded sessions
GET  /sessions/{id}/stats           — analytics for one session
GET  /sessions/{id}/timeline        — raw time-series for charting
GET  /sessions/{id}/report          — generate (or serve cached) PNG report
GET  /sessions/{id}/download        — download raw CSV file
DELETE /sessions/{id}               — delete a session
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import get_session_service
from app.api.schemas import (
    ReportGeneratedResponse,
    SessionStatsResponse,
    SessionSummary,
    SessionTimelineResponse,
)
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get(
    "",
    response_model=list[SessionSummary],
    summary="List all sessions",
)
def list_sessions(
    svc: SessionService = Depends(get_session_service),
) -> list[SessionSummary]:
    """Returns all session CSV files sorted newest-first."""
    return svc.list_sessions()


@router.get(
    "/{session_id}/stats",
    response_model=SessionStatsResponse,
    summary="Session analytics",
)
def get_session_stats(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
) -> SessionStatsResponse:
    """
    Computes and returns full statistics for the given session:
    score, time splits, bad-posture streaks, and best good streak.
    """
    return svc.get_stats(session_id)


@router.get(
    "/{session_id}/timeline",
    response_model=SessionTimelineResponse,
    summary="Raw time-series data",
)
def get_session_timeline(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
) -> SessionTimelineResponse:
    """
    Returns the full per-second posture ratio time-series.
    Suitable for rendering a live-replay chart on the client.
    """
    return svc.get_timeline(session_id)


@router.get(
    "/{session_id}/report",
    response_model=ReportGeneratedResponse,
    summary="Generate session PNG report",
)
def generate_report(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
) -> ReportGeneratedResponse:
    """
    Generates (or returns the cached) PNG report for the session.
    The PNG is saved next to the CSV as ``session_*_report.png``.

    To download the image directly use ``GET /sessions/{id}/report/image``.
    """
    from app.reports.report_generator import generate_report as _gen
    csv_path = svc.resolve_path(session_id)
    png_path = _gen(csv_path=csv_path, show=False)

    return ReportGeneratedResponse(
        session_id = session_id,
        png_path   = png_path,
        message    = "Report generated successfully.",
    )


@router.get(
    "/{session_id}/report/image",
    summary="Download session PNG report image",
    response_class=FileResponse,
)
def download_report_image(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
) -> FileResponse:
    """
    Returns the session report PNG as a downloadable image.
    Generates the PNG first if it doesn't exist yet.
    """
    from app.reports.report_generator import generate_report as _gen
    csv_path = svc.resolve_path(session_id)
    png_path = csv_path.replace(".csv", "_report.png")

    if not os.path.isfile(png_path):
        png_path = _gen(csv_path=csv_path, show=False)

    return FileResponse(
        path         = png_path,
        media_type   = "image/png",
        filename     = os.path.basename(png_path),
    )


@router.get(
    "/{session_id}/download",
    summary="Download raw session CSV",
    response_class=FileResponse,
)
def download_csv(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
) -> FileResponse:
    """Downloads the raw session CSV file."""
    csv_path = svc.resolve_path(session_id)
    return FileResponse(
        path       = csv_path,
        media_type = "text/csv",
        filename   = os.path.basename(csv_path),
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a session",
)
def delete_session(
    session_id: str,
    svc: SessionService = Depends(get_session_service),
) -> None:
    """Deletes the session CSV and its report PNG (if present)."""
    csv_path = svc.resolve_path(session_id)
    png_path = csv_path.replace(".csv", "_report.png")

    os.remove(csv_path)
    if os.path.isfile(png_path):
        os.remove(png_path)
