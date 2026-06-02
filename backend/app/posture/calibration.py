"""
posture/calibration.py — Calibration data persistence and quick-cal state machine.

The :class:`CalibrationManager` is the single owner of all calibration state.
It is updated once per frame during the quick-calibration sequence and exposes
a simple phase property so visualization.py can draw the right overlay.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import numpy as np

from app.config import (
    CALIBRATION_FILE,
    DATA_DIR,
    QUICK_CAL_COLLECT_SECONDS,
    QUICK_CAL_MIN_FRAMES,
    QUICK_CAL_WARMUP_SECONDS,
)


class CalPhase(Enum):
    WARMUP  = auto()
    COLLECT = auto()
    DONE    = auto()


@dataclass
class CalibrationData:
    baseline_distance: float
    baseline_angle: float


class CalibrationManager:
    """
    Manages calibration lifecycle:
    * loads persisted data on startup,
    * runs the two-phase quick-cal sequence frame by frame,
    * saves results to disk.
    """

    def __init__(self) -> None:
        self._data: Optional[CalibrationData] = _load()
        self._phase = CalPhase.DONE if self._data else CalPhase.WARMUP
        self._start_time: Optional[float] = None
        self._distances: list[float] = []
        self._angles: list[float] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_calibrated(self) -> bool:
        return self._data is not None

    @property
    def phase(self) -> CalPhase:
        return self._phase

    @property
    def baseline_distance(self) -> Optional[float]:
        return self._data.baseline_distance if self._data else None

    @property
    def baseline_angle(self) -> Optional[float]:
        return self._data.baseline_angle if self._data else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_recalibration(self) -> None:
        """Reset and begin a fresh quick-calibration sequence."""
        self._data        = None
        self._phase       = CalPhase.WARMUP
        self._start_time  = None
        self._distances.clear()
        self._angles.clear()

    def update(
        self,
        now: float,
        distance: Optional[float],
        angle: Optional[float],
    ) -> tuple[CalPhase, float, int]:
        """
        Advance the calibration state machine.

        Call once per frame only while :attr:`phase` is WARMUP or COLLECT.

        Parameters
        ----------
        now:      current ``time.time()`` value
        distance: measured nose-to-shoulder distance (px), or None if no pose
        angle:    measured head angle (deg), or None if no pose

        Returns
        -------
        (phase, progress, seconds_remaining)
            *progress* is 0.0-1.0 during COLLECT; always 0.0 during WARMUP.
        """
        if self._start_time is None:
            self._start_time = now

        elapsed = now - self._start_time

        if self._phase == CalPhase.WARMUP:
            if elapsed >= QUICK_CAL_WARMUP_SECONDS:
                self._phase = CalPhase.COLLECT
            remaining = max(0, int(QUICK_CAL_WARMUP_SECONDS - elapsed) + 1)
            return CalPhase.WARMUP, 0.0, remaining

        # COLLECT phase
        if distance is not None and angle is not None:
            self._distances.append(distance)
            self._angles.append(angle)

        collect_elapsed = elapsed - QUICK_CAL_WARMUP_SECONDS
        progress  = min(collect_elapsed / QUICK_CAL_COLLECT_SECONDS, 1.0)
        remaining = max(0, int(QUICK_CAL_COLLECT_SECONDS - collect_elapsed) + 1)

        if collect_elapsed >= QUICK_CAL_COLLECT_SECONDS:
            self._finalise()

        return CalPhase.COLLECT, progress, remaining

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _finalise(self) -> None:
        if len(self._distances) >= QUICK_CAL_MIN_FRAMES:
            bd = float(np.mean(self._distances))
            ba = float(np.mean(self._angles))
            self._data = CalibrationData(bd, ba)
            _save(bd, ba)
            print(f"[Calibration] Done - distance: {bd:.1f}px  angle: {ba:.1f} deg")
        else:
            print(
                f"[Calibration] Only {len(self._distances)} frames collected "
                f"(need {QUICK_CAL_MIN_FRAMES}) - restarting."
            )
            self._start_time = None
            self._distances.clear()
            self._angles.clear()
            return

        self._phase = CalPhase.DONE


# ── File I/O helpers (module-level, no state) ──────────────────────────────

def _load() -> Optional[CalibrationData]:
    if not os.path.exists(CALIBRATION_FILE):
        return None
    try:
        with open(CALIBRATION_FILE, "r") as f:
            data = json.load(f)
        bd = data.get("baseline_distance")
        ba = data.get("baseline_angle")
        if bd is None or ba is None:
            return None
        print(f"[Calibration] Loaded - distance: {bd:.1f}  angle: {ba:.1f} deg")
        return CalibrationData(float(bd), float(ba))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[Calibration] Could not load calibration file: {exc}")
        return None


def _save(distance: float, angle: float) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CALIBRATION_FILE, "w") as f:
        json.dump(
            {"baseline_distance": round(distance, 2), "baseline_angle": round(angle, 2)},
            f,
            indent=2,
        )
    print(f"[Calibration] Saved to {CALIBRATION_FILE}")
