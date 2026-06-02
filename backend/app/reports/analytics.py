"""
reports/analytics.py — Statistical calculations derived from session data.

All functions are pure (no I/O, no plotting) so they are easy to unit-test
and can be reused by an API endpoint or a CLI report alike.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.reports.parser import SessionData


@dataclass
class SessionStats:
    """Computed statistics for one session."""
    total_frames:      int
    good_count:        int
    slight_count:      int
    bad_count:         int
    good_pct:          float
    slight_pct:        float
    bad_pct:           float
    score:             float        # weighted 0–100
    duration_min:      float
    bad_streaks:       list[tuple[float, float]]   # [(start_s, end_s), ...]
    top_bad_streaks:   list[tuple[float, float]]   # top-3 longest
    best_good_streak:  float        # seconds


def compute_stats(data: SessionData) -> SessionStats:
    """Derive all report statistics from *data*."""
    statuses = data.statuses
    elapsed  = data.elapsed
    total    = len(statuses)

    good_count   = statuses.count("GOOD POSTURE")
    slight_count = statuses.count("SLIGHT SLOUCH")
    bad_count    = statuses.count("BAD POSTURE")

    good_pct   = good_count   / total * 100
    slight_pct = slight_count / total * 100
    bad_pct    = bad_count    / total * 100

    score        = (good_count * 100 + slight_count * 60) / total
    duration_min = float(elapsed[-1]) / 60

    bad_streaks  = _find_streaks(statuses, elapsed, "BAD POSTURE")
    good_streaks = _find_streaks(statuses, elapsed, "GOOD POSTURE")

    top_bad = sorted(bad_streaks, key=lambda x: x[1] - x[0], reverse=True)[:3]
    best_good = max((t1 - t0 for t0, t1 in good_streaks), default=0.0)

    return SessionStats(
        total_frames     = total,
        good_count       = good_count,
        slight_count     = slight_count,
        bad_count        = bad_count,
        good_pct         = good_pct,
        slight_pct       = slight_pct,
        bad_pct          = bad_pct,
        score            = score,
        duration_min     = duration_min,
        bad_streaks      = bad_streaks,
        top_bad_streaks  = top_bad,
        best_good_streak = best_good,
    )


# ── Helpers ───────────────────────────────────────────────────────────────

def _find_streaks(
    statuses: list[str],
    elapsed: np.ndarray,
    target: str,
) -> list[tuple[float, float]]:
    """Return a list of (start_s, end_s) intervals for *target* status."""
    streaks: list[tuple[float, float]] = []
    in_streak = False
    start_t: float = 0.0

    for i, s in enumerate(statuses):
        if s == target:
            if not in_streak:
                start_t   = float(elapsed[i])
                in_streak = True
        else:
            if in_streak:
                streaks.append((start_t, float(elapsed[i - 1])))
                in_streak = False

    if in_streak:
        streaks.append((start_t, float(elapsed[-1])))

    return streaks
