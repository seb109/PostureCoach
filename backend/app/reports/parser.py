"""
reports/parser.py — Discovers and parses session CSV files.

Keeps all I/O and data-loading logic out of analytics and chart modules.
"""
from __future__ import annotations

import csv
import glob
import os
import sys
from dataclasses import dataclass

import numpy as np

from app.config import SESSION_DIR


@dataclass
class SessionData:
    """Raw arrays from a single session CSV."""
    csv_path:   str
    timestamps: list[str]
    elapsed:    np.ndarray   # float64 seconds
    ratios:     np.ndarray   # float64 %
    distances:  list[float]
    angles:     list[float]
    statuses:   list[str]


def find_latest_csv() -> str:
    """Return path to the most recent session_*.csv, or exit with an error."""
    pattern = os.path.join(SESSION_DIR, "session_*.csv")
    files   = glob.glob(pattern)

    # Fallback: also check CWD for legacy files
    if not files:
        files = glob.glob("session_*.csv")

    if not files:
        print(
            f"No session_*.csv files found in {SESSION_DIR} or current directory.\n"
            "Run pos.py (or main.py) first."
        )
        sys.exit(1)

    return max(files)   # lexicographic sort == chronological sort by filename


def load_session(csv_path: str) -> SessionData:
    """
    Parse *csv_path* and return a :class:`SessionData`.

    Malformed rows are silently skipped.
    Exits if fewer than 2 valid rows are found.
    """
    timestamps, elapsed, ratios, distances, angles, statuses = [], [], [], [], [], []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                timestamps.append(row["timestamp"])
                elapsed.append(float(row["elapsed_s"]))
                ratios.append(float(row["ratio"]))
                distances.append(float(row["distance"]))
                angles.append(float(row["angle"]))
                statuses.append(row["status"])
            except (ValueError, KeyError):
                continue

    if len(elapsed) < 2:
        print(f"Not enough data in {csv_path} (need ≥ 2 rows).")
        sys.exit(1)

    return SessionData(
        csv_path   = csv_path,
        timestamps = timestamps,
        elapsed    = np.array(elapsed, dtype=np.float64),
        ratios     = np.array(ratios,  dtype=np.float64),
        distances  = distances,
        angles     = angles,
        statuses   = statuses,
    )
