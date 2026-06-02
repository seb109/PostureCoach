from __future__ import annotations

import base64

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user, get_posture_service
from app.api.schemas import FrameAnalysisResponse
from app.api.v1.endpoints.stream import _to_schema
from app.models import User

router = APIRouter(prefix="/posture", tags=["posture"])


class AnalyzeFrameRequest(BaseModel):
    image_base64: str


@router.post("/analyze", response_model=FrameAnalysisResponse)
def analyze_frame(payload: AnalyzeFrameRequest, _: User = Depends(get_current_user), svc=Depends(get_posture_service)) -> FrameAnalysisResponse:
    try:
        raw = base64.b64decode(payload.image_base64.split(",")[-1])
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image payload.") from exc
    if frame is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image payload.")
    return _to_schema(svc.process_frame(frame))


@router.get("/live")
def live_info(_: User = Depends(get_current_user)) -> dict[str, str]:
    return {"websocket": "/api/v1/stream", "protocol": "Send JPEG bytes and receive posture JSON."}
