"""
api/v1/endpoints/stream.py — WebSocket endpoint for real-time frame analysis.

Protocol
--------
Client → Server  (binary)
    Raw JPEG bytes of one video frame (e.g. from a webcam via canvas.toBlob()).

Server → Client  (text / JSON)
    FrameAnalysisResponse serialised as JSON.

The client can also send a UTF-8 text message ``"recalibrate"`` at any time
to trigger a new calibration sequence.

Connection lifecycle
--------------------
1. Client connects to ``ws://<host>/api/v1/stream``.
2. Server accepts and starts reading frames.
3. For each binary frame received, the server runs the full pipeline and
   sends back a JSON result.
4. Either side can close the connection; the server logs the session summary.

Error handling
--------------
If a frame cannot be decoded (corrupt JPEG, wrong format) the server sends
a JSON error object and continues — it does **not** close the connection.
"""
from __future__ import annotations

import json
import logging

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps import get_posture_service
from app.api.schemas import FrameAnalysisResponse
from app.posture.calibration import CalPhase
from app.services.posture_service import PostureService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stream"])


@router.websocket("/stream")
async def posture_stream(websocket: WebSocket) -> None:
    """
    WebSocket endpoint — accepts JPEG frames, returns posture analysis JSON.

    See module docstring for the full protocol.
    """
    await websocket.accept()
    svc: PostureService = get_posture_service()
    logger.info("WebSocket client connected.")

    try:
        while True:
            raw = await websocket.receive()

            # ── Text control messages ──────────────────────────────────
            if raw.get("text"):
                text = raw["text"].strip().lower()
                if text == "recalibrate":
                    svc.start_recalibration()
                    await websocket.send_text(
                        json.dumps({"event": "recalibrate_started"})
                    )
                # ignore unknown text messages gracefully
                continue

            # ── Binary frame ───────────────────────────────────────────
            jpeg_bytes: bytes = raw.get("bytes", b"")
            if not jpeg_bytes:
                continue

            bgr = _decode_jpeg(jpeg_bytes)
            if bgr is None:
                await websocket.send_text(
                    json.dumps({"error": "Could not decode frame — expected JPEG bytes."})
                )
                continue

            result = svc.process_frame(bgr)
            response = _to_schema(result)
            await websocket.send_text(response.model_dump_json())

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as exc:
        logger.exception("Unexpected error in WebSocket handler: %s", exc)
        await websocket.close(code=1011)


# ── Helpers ────────────────────────────────────────────────────────────────

def _decode_jpeg(data: bytes):
    """Decode raw JPEG bytes → BGR ndarray, or None on failure."""
    try:
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return frame  # None if imdecode fails
    except Exception:
        return None


def _to_schema(result) -> FrameAnalysisResponse:
    """Convert a FrameResult dataclass into an API response model."""
    return FrameAnalysisResponse(
        cal_phase        = result.cal_phase.name,   # "WARMUP" | "COLLECT" | "DONE"
        cal_progress     = round(result.cal_progress, 3),
        cal_seconds_left = result.cal_seconds_left,

        status           = result.status.value if result.status else None,
        ratio            = round(result.ratio,    2) if result.ratio    is not None else None,
        distance         = round(result.distance, 2) if result.distance is not None else None,
        angle            = round(result.angle,    2) if result.angle    is not None else None,
        pose_visible     = result.pose_visible,

        alert_progress     = round(result.alert_progress, 3),
        alert_seconds_left = result.alert_seconds_left,
        is_flashing        = result.is_flashing,
        cooldown_seconds   = result.cooldown_seconds,
    )
