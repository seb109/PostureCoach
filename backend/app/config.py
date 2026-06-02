"""
config.py — Centralised configuration for PostureCoach.

All tuneable constants live here so nothing is scattered across modules.
"""
from __future__ import annotations
import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR          = os.path.dirname(os.path.dirname(__file__))   # repo root
DATA_DIR          = os.path.join(BASE_DIR, "data")
CALIBRATION_FILE  = os.path.join(DATA_DIR, "calibration.json")
SESSION_DIR       = os.path.join(DATA_DIR, "sessions")

# ── MediaPipe ──────────────────────────────────────────────────────────────
MEDIAPIPE_DETECTION_CONFIDENCE  = 0.7
MEDIAPIPE_TRACKING_CONFIDENCE   = 0.7
LANDMARK_VISIBILITY_THRESHOLD   = 0.5

# ── Calibration ────────────────────────────────────────────────────────────
QUICK_CAL_WARMUP_SECONDS   = 5   # instruction phase
QUICK_CAL_COLLECT_SECONDS  = 5   # data-collection phase
QUICK_CAL_MIN_FRAMES       = 60  # minimum frames to accept calibration

# ── Posture classification thresholds (% of baseline distance) ─────────────
RATIO_GOOD_THRESHOLD   = 85.0   # ratio > 85 → GOOD POSTURE
RATIO_SLIGHT_THRESHOLD = 70.0   # ratio > 70 → SLIGHT SLOUCH, else → BAD

# ── Alert timings ──────────────────────────────────────────────────────────
ALERT_DELAY_BAD_SECONDS    = 10   # sustained BAD before alert fires
ALERT_DELAY_SLIGHT_SECONDS = 20   # sustained SLIGHT before alert fires
ALERT_COOLDOWN_SECONDS     = 20   # minimum gap between consecutive alerts
ALERT_FLASH_DURATION       = 3.0  # seconds to flash red border

# ── Session logging ────────────────────────────────────────────────────────
LOG_INTERVAL_SECONDS = 1.0   # one CSV row per second

# ── Report colours ─────────────────────────────────────────────────────────
COLOR_GOOD   = "#00DC64"
COLOR_SLIGHT = "#FFA040"
COLOR_BAD    = "#FF4444"
BG_DARK      = "#0f0f1a"
BG_PANEL     = "#16162a"
TEXT_DIM     = "#888899"
TEXT_BRIGHT  = "#e8e8f0"
