"""
posture/visualization.py — OpenCV drawing helpers for the live HUD.

All frame-mutation code lives here so main.py stays free of cv2 calls.
Every function takes *frame* as its first argument and mutates it in-place.
"""
from __future__ import annotations

import cv2
import numpy as np

from app.posture.calibration import CalPhase
from app.posture.classifier import PostureStatus, STATUS_BGR


# ── Calibration overlays ───────────────────────────────────────────────────

def draw_cal_warmup(frame, seconds_remaining: int) -> None:
    """Phase-1: dim the frame and show the 'SIT UP TALL' instruction."""
    fh, fw = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, fh // 2 - 90), (fw, fh // 2 + 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    cv2.putText(
        frame, "SIT UP TALL",
        (fw // 2 - 160, fh // 2 - 40),
        cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 220, 100), 3,
    )
    cv2.putText(
        frame, f"Calibrating in {seconds_remaining}s...",
        (fw // 2 - 165, fh // 2 + 15),
        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (200, 200, 200), 2,
    )


def draw_cal_collect(frame, progress: float, seconds_remaining: int) -> None:
    """Phase-2: dim the frame and show the progress bar."""
    fh, fw = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, fh // 2 - 90), (fw, fh // 2 + 80), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    cv2.putText(
        frame, "HOLD STILL",
        (fw // 2 - 140, fh // 2 - 40),
        cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 220, 100), 3,
    )
    draw_progress_bar(frame, progress, y=fh // 2 - 10, h_bar=16, color=(0, 220, 100))
    cv2.putText(
        frame, f"{seconds_remaining}s",
        (fw // 2 - 18, fh // 2 + 38),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2,
    )


# ── Detection HUD ──────────────────────────────────────────────────────────

def draw_keypoint_overlay(
    frame,
    nose: tuple,
    l_shoulder: tuple,
    r_shoulder: tuple,
    mid_shoulder: tuple,
    status: PostureStatus,
) -> None:
    """Draw the nose→mid-shoulder line and landmark circles."""
    color = STATUS_BGR[status]
    cv2.line(frame, nose, mid_shoulder, (255, 255, 0), 2)
    for pt in [nose, l_shoulder, r_shoulder, mid_shoulder]:
        cv2.circle(frame, pt, 8, color, -1)


def draw_metrics_hud(
    frame,
    distance: float,
    baseline_distance: float,
    angle: float,
    ratio: float,
    status: PostureStatus,
) -> None:
    """Top-left metric readout."""
    color = STATUS_BGR[status]
    cv2.putText(frame,
                f"Dist : {distance:.1f}  (baseline {baseline_distance:.1f})",
                (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
    cv2.putText(frame, f"Angle: {angle:.1f} deg",
                (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
    cv2.putText(frame, f"Ratio: {ratio:.1f}%",
                (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
    cv2.putText(frame, status.value,
                (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)


def draw_alert_bar(
    frame,
    progress: float,
    seconds_left: int,
    status: PostureStatus,
) -> None:
    """Bottom alert charge bar."""
    if progress <= 0:
        return
    fh = frame.shape[0]
    bar_color = (0, 0, 255) if status == PostureStatus.BAD else (0, 130, 255)
    draw_progress_bar(frame, progress, y=fh - 50, h_bar=12, color=bar_color)
    label = f"Alert in {seconds_left}s" if seconds_left > 0 else "ALERTING!"
    cv2.putText(frame, label, (30, fh - 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, bar_color, 1)


def draw_cooldown_badge(frame, seconds_left: int) -> None:
    if seconds_left <= 0:
        return
    fh, fw = frame.shape[:2]
    cv2.putText(frame, f"Cooldown {seconds_left}s",
                (fw - 175, fh - 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (160, 160, 160), 1)


def draw_flash_alert(frame, blink_on: bool) -> None:
    """Red border + 'SIT UP!' text when an alert is active."""
    fh, fw = frame.shape[:2]
    if blink_on:
        draw_border(frame, (0, 0, 255), thickness=12)
    cv2.putText(frame, "SIT UP!",
                (fw // 2 - 100, fh // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 0, 255), 5)


def draw_no_pose_warning(frame) -> None:
    cv2.putText(frame, "Move back into frame",
                (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)


def draw_footer(frame) -> None:
    fh = frame.shape[0]
    cv2.putText(frame, "C = recalibrate   |   Q = quit",
                (30, fh - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (150, 150, 150), 1)


# ── Primitives ─────────────────────────────────────────────────────────────

def draw_progress_bar(
    frame,
    progress: float,
    y: int,
    h_bar: int = 14,
    color: tuple = (0, 220, 100),
) -> None:
    fw = frame.shape[1]
    x1, x2  = 30, fw - 30
    filled   = int(progress * (x2 - x1))
    cv2.rectangle(frame, (x1, y), (x2, y + h_bar), (55, 55, 55), -1)
    if filled > 0:
        cv2.rectangle(frame, (x1, y), (x1 + filled, y + h_bar), color, -1)
    cv2.rectangle(frame, (x1, y), (x2, y + h_bar), (140, 140, 140), 1)


def draw_border(frame, color: tuple, thickness: int = 10) -> None:
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, thickness)
