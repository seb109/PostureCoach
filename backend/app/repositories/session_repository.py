from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import PostureMetric, Session as PostureSession


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: str) -> PostureSession:
        session = PostureSession(user_id=user_id)
        self.db.add(session)
        self.db.flush()
        return session

    def get_for_user(self, session_id: str, user_id: str) -> PostureSession | None:
        stmt = (
            select(PostureSession)
            .options(selectinload(PostureSession.metrics), selectinload(PostureSession.report))
            .where(PostureSession.id == session_id, PostureSession.user_id == user_id)
        )
        return self.db.scalar(stmt)

    def list_for_user(self, user_id: str) -> list[PostureSession]:
        stmt = (
            select(PostureSession)
            .options(selectinload(PostureSession.metrics), selectinload(PostureSession.report))
            .where(PostureSession.user_id == user_id)
            .order_by(PostureSession.started_at.desc())
        )
        return list(self.db.scalars(stmt))

    def add_metric(self, session: PostureSession, score: float, classification: str, ratio: float | None, distance: float | None, angle: float | None, alert: str | None) -> PostureMetric:
        metric = PostureMetric(session_id=session.id, score=score, classification=classification, ratio=ratio, distance=distance, angle=angle, alert=alert)
        self.db.add(metric)
        self.db.flush()
        return metric

    def stop(self, session: PostureSession) -> PostureSession:
        now = datetime.now(timezone.utc)
        started_at = session.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        session.ended_at = now
        session.status = "completed"
        session.duration_seconds = max(0, int((now - started_at).total_seconds()))
        avg = self.db.scalar(select(func.avg(PostureMetric.score)).where(PostureMetric.session_id == session.id))
        session.average_score = round(float(avg or 0), 2)
        self.db.flush()
        self.db.refresh(session, attribute_names=["metrics", "report"])
        return session
