"""
posture/alerts.py — Alert state machine and sound playback.

The :class:`AlertManager` tracks how long the user has been in a bad or
slight-slouch state and fires an audible alert when the configured delay
is exceeded.  Sound is played in a daemon thread so it never blocks the
camera loop.

Platform note
-------------
``winsound`` is Windows-only.  On macOS/Linux the alert silently no-ops
unless you swap in a cross-platform library such as ``playsound`` or
``pygame``.  The fallback path prints a console warning so the rest of the
app continues to function on non-Windows hosts.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

from app.config import (
    ALERT_COOLDOWN_SECONDS,
    ALERT_DELAY_BAD_SECONDS,
    ALERT_DELAY_SLIGHT_SECONDS,
    ALERT_FLASH_DURATION,
)
from app.posture.classifier import PostureStatus

# ── Platform-safe sound import ─────────────────────────────────────────────
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False


class AlertManager:
    """
    Tracks posture-streak timers and fires alerts.

    Typical call pattern per frame::

        am.update(status, now)
        progress, seconds_left = am.alert_progress(status, now)
        if am.is_flashing(now):
            draw_flash_border(frame)
    """

    def __init__(self) -> None:
        self._bad_start:    Optional[float] = None
        self._slight_start: Optional[float] = None
        self._last_alert:   Optional[float] = None
        self._flash_until:  Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all timers (called after recalibration)."""
        self._bad_start    = None
        self._slight_start = None
        self._last_alert   = None
        self._flash_until  = None

    def update(self, status: PostureStatus, now: float) -> None:
        """
        Advance streak timers and fire an alert if a threshold is crossed.

        Must be called once per detected frame.
        """
        self._update_streak_timers(status, now)

        cooldown_ok = self._cooldown_ok(now)
        if not cooldown_ok:
            return

        if status == PostureStatus.BAD:
            time_in_bad = self._elapsed(self._bad_start, now)
            if time_in_bad >= ALERT_DELAY_BAD_SECONDS:
                self._fire(now)
                self._bad_start = None
                print("[Alert] BAD POSTURE sustained too long!")

        elif status == PostureStatus.SLIGHT:
            time_in_slight = self._elapsed(self._slight_start, now)
            if time_in_slight >= ALERT_DELAY_SLIGHT_SECONDS:
                self._fire(now)
                self._slight_start = None
                print("[Alert] SLIGHT SLOUCH sustained too long!")

    def alert_progress(self, status: PostureStatus, now: float) -> tuple[float, int]:
        """
        Return (progress 0-1, seconds_remaining) for the alert charge bar.

        Returns (0.0, 0) when cooldown is active or status is GOOD.
        """
        if not self._cooldown_ok(now):
            return 0.0, 0

        if status == PostureStatus.BAD:
            elapsed = self._elapsed(self._bad_start, now)
            progress = min(elapsed / ALERT_DELAY_BAD_SECONDS, 1.0)
            remaining = max(0, int(ALERT_DELAY_BAD_SECONDS - elapsed))
            return progress, remaining

        if status == PostureStatus.SLIGHT:
            elapsed = self._elapsed(self._slight_start, now)
            progress = min(elapsed / ALERT_DELAY_SLIGHT_SECONDS, 1.0)
            remaining = max(0, int(ALERT_DELAY_SLIGHT_SECONDS - elapsed))
            return progress, remaining

        return 0.0, 0

    def is_flashing(self, now: float) -> bool:
        return self._flash_until is not None and now < self._flash_until

    def flash_blink_on(self, now: float) -> bool:
        """~5 Hz blink logic; True when the border should be drawn."""
        if not self.is_flashing(now):
            return False
        return int((self._flash_until - now) * 5) % 2 == 0  # type: ignore[operator]

    def cooldown_seconds_left(self, now: float) -> int:
        if self._last_alert is None:
            return 0
        left = ALERT_COOLDOWN_SECONDS - (now - self._last_alert)
        return max(0, int(left))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_streak_timers(self, status: PostureStatus, now: float) -> None:
        if status == PostureStatus.GOOD:
            self._bad_start    = None
            self._slight_start = None
        elif status == PostureStatus.SLIGHT:
            self._bad_start = None
            if self._slight_start is None:
                self._slight_start = now
        else:  # BAD
            self._slight_start = None
            if self._bad_start is None:
                self._bad_start = now

    def _fire(self, now: float) -> None:
        self._last_alert  = now
        self._flash_until = now + ALERT_FLASH_DURATION
        play_alert()

    def _cooldown_ok(self, now: float) -> bool:
        return (
            self._last_alert is None
            or (now - self._last_alert) >= ALERT_COOLDOWN_SECONDS
        )

    @staticmethod
    def _elapsed(start: Optional[float], now: float) -> float:
        return (now - start) if start is not None else 0.0


# ── Sound playback ─────────────────────────────────────────────────────────

def play_alert() -> None:
    """Fire a non-blocking 5-beep alert."""
    threading.Thread(target=_beep, daemon=True).start()


def _beep() -> None:
    if _HAS_WINSOUND:
        for _ in range(5):
            winsound.Beep(880, 350)
            time.sleep(0.08)
    else:
        print("\a\a\a")   # terminal bell fallback
