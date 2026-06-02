"""
services/session_service.py — Business logic for session file management.

Provides listing, loading, and stats generation over persisted CSV sessions.
Keeps all filesystem and analytics logic out of the route layer.
"""
from __future__ import annotations

import glob
import os
import re
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from app.api.schemas import (
    SessionStatsResponse,
    SessionSummary,
    SessionTimelinePoint,
    SessionTimelineResponse,
    StreakInterval,
)
from app import config
from app.reports.analytics import compute_stats
from app.reports.parser import load_session


_SESSION_RE = re.compile(r"session_(\d{8})_(\d{6})\.csv$")


class SessionService:
    """Stateless helper — safe to construct per-request."""

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_sessions(self) -> list[SessionSummary]:
        try:
            os.makedirs(config.SESSION_DIR, exist_ok=True)
        except OSError:
            return []
        pattern = os.path.join(config.SESSION_DIR, "session_*.csv")
        files   = sorted(glob.glob(pattern), reverse=True)   # newest first

        result = []
        for path in files:
            filename = os.path.basename(path)
            recorded_at = _parse_recorded_at(filename)
            result.append(SessionSummary(
                filename    = filename,
                recorded_at = recorded_at,
                size_bytes  = os.path.getsize(path),
            ))
        return result

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self, session_id: str) -> SessionStatsResponse:
        path = self._resolve(session_id)
        data  = load_session(path)
        stats = compute_stats(data)

        top_bad = [
            StreakInterval(start_s=t0, end_s=t1, duration_s=round(t1 - t0, 1))
            for t0, t1 in stats.top_bad_streaks
        ]

        return SessionStatsResponse(
            session_id         = session_id,
            duration_min       = round(stats.duration_min, 2),
            total_frames       = stats.total_frames,
            score              = round(stats.score, 1),
            good_count         = stats.good_count,
            slight_count       = stats.slight_count,
            bad_count          = stats.bad_count,
            good_pct           = round(stats.good_pct, 1),
            slight_pct         = round(stats.slight_pct, 1),
            bad_pct            = round(stats.bad_pct, 1),
            bad_streak_count   = len(stats.bad_streaks),
            top_bad_streaks    = top_bad,
            best_good_streak_s = round(stats.best_good_streak, 1),
        )

    # ------------------------------------------------------------------
    # Timeline (raw time-series for charting)
    # ------------------------------------------------------------------

    def get_timeline(self, session_id: str) -> SessionTimelineResponse:
        path = self._resolve(session_id)
        data = load_session(path)

        points = [
            SessionTimelinePoint(
                elapsed_s = float(data.elapsed[i]),
                ratio     = float(data.ratios[i]),
                status    = data.statuses[i],
            )
            for i in range(len(data.elapsed))
        ]

        return SessionTimelineResponse(session_id=session_id, points=points)

    # ------------------------------------------------------------------
    # CSV path resolution
    # ------------------------------------------------------------------

    def resolve_path(self, session_id: str) -> str:
        return self._resolve(session_id)

    def _resolve(self, session_id: str) -> str:
        """
        Turn a session_id (filename stem or full filename) into an absolute path.
        Raises 404 if not found.
        """
        # Accept both "session_20260101_120000" and "session_20260101_120000.csv"
        name = session_id if session_id.endswith(".csv") else f"{session_id}.csv"
        path = os.path.join(config.SESSION_DIR, name)

        if not os.path.isfile(path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )
        return path


# ── Helpers ───────────────────────────────────────────────────────────────

def _parse_recorded_at(filename: str) -> str:
    m = _SESSION_RE.search(filename)
    if not m:
        return "unknown"
    try:
        dt = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
        return dt.isoformat()
    except ValueError:
        return "unknown"
