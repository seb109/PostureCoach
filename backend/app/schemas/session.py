from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PostureMetricCreate(BaseModel):
    session_id: str
    score: float = Field(ge=0, le=100)
    classification: str
    ratio: float | None = None
    distance: float | None = None
    angle: float | None = None
    alert: str | None = None


class PostureMetricRead(BaseModel):
    id: str
    captured_at: datetime
    score: float
    classification: str
    ratio: float | None
    distance: float | None
    angle: float | None
    alert: str | None

    model_config = {"from_attributes": True}


class SessionRead(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    average_score: float
    status: str
    report_id: str | None = None
    metrics: list[PostureMetricRead] = []

    model_config = {"from_attributes": True}


class SessionStartResponse(BaseModel):
    session: SessionRead


class SessionStopResponse(BaseModel):
    session: SessionRead
    report_id: str | None = None


class SessionStats(BaseModel):
    total_sessions: int
    total_minutes: float
    average_score: float
    good_percentage: float
    slight_percentage: float
    bad_percentage: float
