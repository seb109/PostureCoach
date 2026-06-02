"""
posture/session_logger.py — Writes per-second posture data to a CSV file.

The :class:`SessionLogger` opens the CSV on construction and must be closed
(or used as a context manager) to flush and release the file handle.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Optional

from app.config import DATA_DIR, LOG_INTERVAL_SECONDS, SESSION_DIR
from app.posture.classifier import PostureStatus


class SessionLogger:
    """
    Throttled CSV writer — one row per :data:`~app.config.LOG_INTERVAL_SECONDS`.

    Usage::

        with SessionLogger() as logger:
            logger.log(now, ratio, distance, angle, status)
    """

    CSV_HEADER = ["timestamp", "elapsed_s", "ratio", "distance", "angle", "status"]

    def __init__(self) -> None:
        os.makedirs(SESSION_DIR, exist_ok=True)
        dt = datetime.now()
        self.filename = os.path.join(
            SESSION_DIR, dt.strftime("session_%Y%m%d_%H%M%S.csv")
        )
        self._file   = open(self.filename, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.CSV_HEADER)

        self._session_start: Optional[float] = None
        self._last_log:      Optional[float] = None
        self._row_count = 0

        print(f"[SessionLogger] Writing to {self.filename}")

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log(
        self,
        now: float,
        ratio: float,
        distance: float,
        angle: float,
        status: PostureStatus,
    ) -> bool:
        """
        Write a row if the throttle interval has elapsed.

        Returns True when a row was actually written.
        """
        if self._session_start is None:
            self._session_start = now

        if self._last_log is not None and (now - self._last_log) < LOG_INTERVAL_SECONDS:
            return False

        elapsed_s = round(now - self._session_start, 1)
        self._writer.writerow([
            datetime.now().strftime("%H:%M:%S"),
            elapsed_s,
            round(ratio, 1),
            round(distance, 1),
            round(angle, 1),
            status.value,
        ])
        self._file.flush()
        self._last_log = now
        self._row_count += 1
        return True

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()
            if self._session_start is not None:
                print(
                    f"[SessionLogger] Session closed - {self._row_count} rows "
                    f"written to {self.filename}"
                )
            else:
                print("[SessionLogger] No data recorded (calibration only).")

    @property
    def has_data(self) -> bool:
        return self._row_count > 0
