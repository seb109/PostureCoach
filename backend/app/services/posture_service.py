"""
services/posture_service.py — Per-frame posture analysis orchestration.

:class:`PostureService` is the single coordinator that the main loop calls.
It owns:
  * PoseDetector       — MediaPipe inference
  * CalibrationManager — calibration state machine
  * AlertManager       — streak timers & sound
  * SessionLogger      — CSV writer

The main loop only needs to call :meth:`process_frame` and read back a
:class:`FrameResult` to know what to draw.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import cv2

from app.posture.alerts import AlertManager
from app.posture.calibration import CalibrationManager, CalPhase
from app.posture.classifier import PostureStatus, classify
from app.posture.detector import (
    PoseDetector,
    compute_ratio,
    get_angle,
    get_distance,
)
from app.posture.session_logger import SessionLogger


@dataclass
class FrameResult:
    """Everything the renderer needs for one processed frame."""
    # Calibration
    cal_phase:          CalPhase
    cal_progress:       float         # 0–1 during COLLECT
    cal_seconds_left:   int

    # Detection (None when pose not found or still calibrating)
    status:             Optional[PostureStatus]
    ratio:              Optional[float]
    distance:           Optional[float]
    angle:              Optional[float]
    nose:               Optional[tuple]
    l_shoulder:         Optional[tuple]
    r_shoulder:         Optional[tuple]
    mid_shoulder:       Optional[tuple]

    # Alerts
    alert_progress:     float
    alert_seconds_left: int
    is_flashing:        bool
    flash_blink_on:     bool
    cooldown_seconds:   int

    # Misc
    pose_visible:       bool


class PostureService:
    """
    Main application service — call :meth:`process_frame` once per loop.

    Usage::

        service = PostureService()
        with service:
            while cap.isOpened():
                ret, bgr = cap.read()
                result = service.process_frame(bgr)
                # ... draw result ...
    """

    def __init__(self) -> None:
        self._detector   = PoseDetector()
        self._calibration = CalibrationManager()
        self._alert      = AlertManager()
        self._logger     = SessionLogger()
        self._baseline_distance: Optional[float] = self._calibration.baseline_distance

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        self._detector.close()
        self._logger.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_recalibration(self) -> None:
        """Trigger a fresh quick-calibration sequence."""
        self._calibration.start_recalibration()
        self._alert.reset()
        self._baseline_distance = None
        print("[PostureService] Recalibration started.")

    def process_frame(self, bgr_frame) -> FrameResult:
        """Run the full pipeline on one BGR camera frame."""
        now = time.time()
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_results = self._detector.process(rgb)
        fh, fw = bgr_frame.shape[:2]

        # ── Extract pose ──────────────────────────────────────────────
        pose_visible = False
        keypoints    = None
        distance = angle = ratio = None

        if mp_results.pose_landmarks:
            self._detector.draw_landmarks(bgr_frame, mp_results.pose_landmarks)
            keypoints = self._detector.extract_keypoints(
                mp_results.pose_landmarks, fw, fh
            )
            if keypoints:
                pose_visible = True
                nose, l_shoulder, r_shoulder, mid_shoulder = keypoints
                distance = get_distance(nose, mid_shoulder)
                angle    = get_angle(nose, mid_shoulder)

        # ── Calibration phase ─────────────────────────────────────────
        phase = self._calibration.phase
        cal_progress = 0.0
        cal_remaining = 0

        if phase != CalPhase.DONE:
            cal_dist  = distance if pose_visible else None
            cal_angle = angle    if pose_visible else None
            phase, cal_progress, cal_remaining = self._calibration.update(
                now, cal_dist, cal_angle
            )
            if phase == CalPhase.DONE:
                self._baseline_distance = self._calibration.baseline_distance

            return FrameResult(
                cal_phase=phase, cal_progress=cal_progress,
                cal_seconds_left=cal_remaining,
                status=None, ratio=None, distance=None, angle=None,
                nose=None, l_shoulder=None, r_shoulder=None, mid_shoulder=None,
                alert_progress=0.0, alert_seconds_left=0,
                is_flashing=False, flash_blink_on=False, cooldown_seconds=0,
                pose_visible=pose_visible,
            )

        # ── Detection / classification ────────────────────────────────
        status = None
        alert_progress = alert_seconds_left = 0
        nose = l_shoulder = r_shoulder = mid_shoulder = None

        if pose_visible and self._baseline_distance:
            nose, l_shoulder, r_shoulder, mid_shoulder = keypoints  # type: ignore[misc]
            ratio  = compute_ratio(distance, self._baseline_distance)  # type: ignore[arg-type]
            status = classify(ratio)

            self._alert.update(status, now)
            self._logger.log(now, ratio, distance, angle, status)  # type: ignore[arg-type]

            alert_progress, alert_seconds_left = self._alert.alert_progress(status, now)

        return FrameResult(
            cal_phase=CalPhase.DONE, cal_progress=1.0, cal_seconds_left=0,
            status=status,
            ratio=ratio, distance=distance, angle=angle,
            nose=nose, l_shoulder=l_shoulder,
            r_shoulder=r_shoulder, mid_shoulder=mid_shoulder,
            alert_progress=alert_progress,
            alert_seconds_left=alert_seconds_left,
            is_flashing=self._alert.is_flashing(now),
            flash_blink_on=self._alert.flash_blink_on(now),
            cooldown_seconds=self._alert.cooldown_seconds_left(now),
            pose_visible=pose_visible,
        )
