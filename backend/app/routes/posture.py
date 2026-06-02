"""
routes/posture.py — CLI sub-command dispatchers.

These thin functions are the public entry points called by main.py.
Keeping them here means main.py stays minimal and future web-route
adapters can import the same logic without touching the service layer.
"""
from __future__ import annotations

import sys


def run_live_session() -> None:
    """Start the live webcam posture-monitoring loop."""
    import cv2
    from app.posture.calibration import CalPhase
    from app.posture.visualization import (
        draw_alert_bar,
        draw_cal_collect,
        draw_cal_warmup,
        draw_cooldown_badge,
        draw_flash_alert,
        draw_footer,
        draw_keypoint_overlay,
        draw_metrics_hud,
        draw_no_pose_warning,
    )
    from app.services.posture_service import PostureService

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open camera.")
        sys.exit(1)

    with PostureService() as service:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("c"):
                service.start_recalibration()

            result = service.process_frame(frame)

            # ── Draw calibration overlays ──────────────────────────────
            if result.cal_phase == CalPhase.WARMUP:
                draw_cal_warmup(frame, result.cal_seconds_left)

            elif result.cal_phase == CalPhase.COLLECT:
                draw_cal_collect(frame, result.cal_progress, result.cal_seconds_left)

            # ── Draw detection HUD ────────────────────────────────────
            elif result.cal_phase == CalPhase.DONE:
                if result.pose_visible and result.status is not None:
                    draw_keypoint_overlay(
                        frame,
                        result.nose, result.l_shoulder,
                        result.r_shoulder, result.mid_shoulder,
                        result.status,
                    )
                    draw_metrics_hud(
                        frame,
                        result.distance, service._calibration.baseline_distance,
                        result.angle, result.ratio, result.status,
                    )
                    if result.alert_progress > 0:
                        draw_alert_bar(
                            frame,
                            result.alert_progress,
                            result.alert_seconds_left,
                            result.status,
                        )
                    draw_cooldown_badge(frame, result.cooldown_seconds)
                else:
                    draw_no_pose_warning(frame)

                if result.is_flashing:
                    draw_flash_alert(frame, result.flash_blink_on)

                draw_footer(frame)

            cv2.imshow("PostureCoach", frame)

    cap.release()
    cv2.destroyAllWindows()
    print("\n[Session] Ended.  Run: python main.py report")


def run_report(csv_path: str | None = None) -> None:
    """Generate a session report PNG (and display it)."""
    from app.reports.report_generator import generate_report
    generate_report(csv_path=csv_path, show=True)
