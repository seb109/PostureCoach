"""
posture/classifier.py — Classifies a posture ratio into a status label.

Keeps thresholds in one place and returns typed results so the rest of the
codebase never hard-codes "GOOD POSTURE" strings.
"""
from __future__ import annotations

from enum import Enum

from app.config import RATIO_GOOD_THRESHOLD, RATIO_SLIGHT_THRESHOLD


class PostureStatus(str, Enum):
    GOOD   = "GOOD POSTURE"
    SLIGHT = "SLIGHT SLOUCH"
    BAD    = "BAD POSTURE"


# BGR colour for each status (used by visualization.py)
STATUS_BGR: dict[PostureStatus, tuple[int, int, int]] = {
    PostureStatus.GOOD:   (0, 220, 100),
    PostureStatus.SLIGHT: (0, 165, 255),
    PostureStatus.BAD:    (0,   0, 255),
}


def classify(ratio: float) -> PostureStatus:
    """
    Return a :class:`PostureStatus` for the given posture *ratio*.

    Parameters
    ----------
    ratio:
        Distance as a percentage of the calibrated baseline (e.g. 92.4).
    """
    if ratio > RATIO_GOOD_THRESHOLD:
        return PostureStatus.GOOD
    if ratio > RATIO_SLIGHT_THRESHOLD:
        return PostureStatus.SLIGHT
    return PostureStatus.BAD
