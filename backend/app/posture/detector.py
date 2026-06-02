"""
posture/detector.py — Pose detection and geometric feature extraction.

Responsibilities
----------------
* Initialise and own the MediaPipe Pose instance.
* Extract the three key landmarks (nose, left shoulder, right shoulder).
* Compute distance, angle, and posture ratio from raw pixel coordinates.
* Validate landmark visibility and screen-boundary conditions.
"""
from __future__ import annotations

import numpy as np
import mediapipe as mp

from app.config import (
    MEDIAPIPE_DETECTION_CONFIDENCE,
    MEDIAPIPE_TRACKING_CONFIDENCE,
    LANDMARK_VISIBILITY_THRESHOLD,
)

# ── MediaPipe singletons ───────────────────────────────────────────────────
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


class PoseDetector:
    """Wraps MediaPipe Pose and exposes clean feature-extraction methods."""

    def __init__(self) -> None:
        self._pose = mp_pose.Pose(
            min_detection_confidence=MEDIAPIPE_DETECTION_CONFIDENCE,
            min_tracking_confidence=MEDIAPIPE_TRACKING_CONFIDENCE,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, rgb_frame):
        """Run pose estimation on an RGB frame and return raw results."""
        return self._pose.process(rgb_frame)

    def draw_landmarks(self, bgr_frame, landmarks) -> None:
        """Overlay skeleton on *bgr_frame* in-place."""
        mp_draw.draw_landmarks(bgr_frame, landmarks, mp_pose.POSE_CONNECTIONS)

    def extract_keypoints(self, landmarks, frame_w: int, frame_h: int):
        """
        Pull nose + shoulders from a landmark list.

        Returns
        -------
        tuple[tuple, tuple, tuple, tuple] | None
            (nose, l_shoulder, r_shoulder, mid_shoulder) as (x, y) pixel
            tuples, or None if any landmark is invalid / out-of-frame.
        """
        lm = landmarks.landmark
        key_lm = [lm[0], lm[11], lm[12]]   # nose, left shoulder, right shoulder

        if not all(self._is_valid(l, frame_w, frame_h) for l in key_lm):
            return None

        nose       = self._to_px(lm[0],  frame_w, frame_h)
        l_shoulder = self._to_px(lm[11], frame_w, frame_h)
        r_shoulder = self._to_px(lm[12], frame_w, frame_h)
        mid_shoulder = get_midpoint(l_shoulder, r_shoulder)

        return nose, l_shoulder, r_shoulder, mid_shoulder

    def close(self) -> None:
        self._pose.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_valid(landmark, frame_w: int, frame_h: int) -> bool:
        x = int(landmark.x * frame_w)
        y = int(landmark.y * frame_h)
        return (
            landmark.visibility > LANDMARK_VISIBILITY_THRESHOLD
            and 0 <= x <= frame_w
            and 0 <= y <= frame_h
        )

    @staticmethod
    def _to_px(landmark, frame_w: int, frame_h: int) -> tuple[int, int]:
        return int(landmark.x * frame_w), int(landmark.y * frame_h)


# ── Standalone geometry helpers (pure functions, easy to unit-test) ─────────

def get_midpoint(p1: tuple, p2: tuple) -> tuple[int, int]:
    return (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2))


def get_distance(p1: tuple, p2: tuple) -> float:
    return float(np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2))


def get_angle(nose: tuple, mid_shoulder: tuple) -> float:
    """Angle (degrees) between nose→mid-shoulder vector and vertical axis."""
    head_vec = np.array([nose[0] - mid_shoulder[0], nose[1] - mid_shoulder[1]])
    vertical = np.array([0, -1])
    mag = np.linalg.norm(head_vec)
    if mag == 0:
        return 0.0
    dot = np.dot(head_vec, vertical)
    return float(np.degrees(np.arccos(np.clip(dot / mag, -1.0, 1.0))))


def compute_ratio(distance: float, baseline_distance: float) -> float:
    """Posture ratio as a percentage of the calibrated baseline distance."""
    return (distance / baseline_distance) * 100
