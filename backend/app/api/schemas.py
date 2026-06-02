"""
api/schemas.py — Pydantic request and response models.

Every API boundary is typed here.  Internal dataclasses (FrameResult,
SessionStats, etc.) are converted to these models at the route layer so
the rest of the app stays free of FastAPI/Pydantic imports.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Shared / enums ─────────────────────────────────────────────────────────

class PostureStatusSchema(str):
    GOOD   = "GOOD POSTURE"
    SLIGHT = "SLIGHT SLOUCH"
    BAD    = "BAD POSTURE"


# ── Calibration ────────────────────────────────────────────────────────────

class CalibrationStatusResponse(BaseModel):
    is_calibrated:     bool
    baseline_distance: Optional[float] = None
    baseline_angle:    Optional[float] = None


class RecalibrateResponse(BaseModel):
    message: str


# ── Frame analysis (WebSocket + REST) ──────────────────────────────────────

class FrameAnalysisResponse(BaseModel):
    """Returned for each processed video frame."""
    # Calibration state
    cal_phase:        str            # "WARMUP" | "COLLECT" | "DONE"
    cal_progress:     float          # 0.0 – 1.0
    cal_seconds_left: int

    # Posture reading (null while calibrating or pose not visible)
    status:           Optional[str]  = None   # PostureStatus value
    ratio:            Optional[float] = None
    distance:         Optional[float] = None
    angle:            Optional[float] = None
    pose_visible:     bool           = False

    # Alert state
    alert_progress:     float = 0.0
    alert_seconds_left: int   = 0
    is_flashing:        bool  = False
    cooldown_seconds:   int   = 0


# ── Sessions ───────────────────────────────────────────────────────────────

class SessionSummary(BaseModel):
    """Lightweight listing item for GET /sessions."""
    filename:     str
    recorded_at:  str   # ISO datetime string parsed from filename
    size_bytes:   int


class StreakInterval(BaseModel):
    start_s: float
    end_s:   float
    duration_s: float


class SessionStatsResponse(BaseModel):
    """Full analytics for one session (GET /sessions/{id}/stats)."""
    session_id:       str
    duration_min:     float
    total_frames:     int
    score:            float

    good_count:       int
    slight_count:     int
    bad_count:        int
    good_pct:         float
    slight_pct:       float
    bad_pct:          float

    bad_streak_count: int
    top_bad_streaks:  list[StreakInterval]
    best_good_streak_s: float


class SessionTimelinePoint(BaseModel):
    elapsed_s: float
    ratio:     float
    status:    str


class SessionTimelineResponse(BaseModel):
    """Raw time-series for charting (GET /sessions/{id}/timeline)."""
    session_id: str
    points:     list[SessionTimelinePoint]


# ── Report ─────────────────────────────────────────────────────────────────

class ReportGeneratedResponse(BaseModel):
    session_id: str
    png_path:   str
    message:    str


# ── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:  str = "ok"
    version: str = "1.0.0"
