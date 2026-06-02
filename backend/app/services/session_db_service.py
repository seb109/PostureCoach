from __future__ import annotations

from collections import Counter

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Session as PostureSession, User
from app.repositories import SessionRepository
from app.schemas import PostureMetricCreate, SessionStats


class SessionDbService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sessions = SessionRepository(db)

    def start(self, user: User) -> PostureSession:
        session = self.sessions.create(user.id)
        self.db.commit()
        self.db.refresh(session)
        return session

    def stop(self, user: User, session_id: str) -> PostureSession:
        session = self._get(user, session_id)
        if session.status != "completed":
            self.sessions.stop(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list(self, user: User) -> list[PostureSession]:
        return self.sessions.list_for_user(user.id)

    def get(self, user: User, session_id: str) -> PostureSession:
        return self._get(user, session_id)

    def record_metric(self, user: User, payload: PostureMetricCreate):
        session = self._get(user, payload.session_id)
        if session.status != "active":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not active.")
        metric = self.sessions.add_metric(
            session=session,
            score=payload.score,
            classification=payload.classification,
            ratio=payload.ratio,
            distance=payload.distance,
            angle=payload.angle,
            alert=payload.alert,
        )
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def stats(self, user: User) -> SessionStats:
        sessions = self.list(user)
        metrics = [metric for session in sessions for metric in session.metrics]
        total_minutes = round(sum(s.duration_seconds for s in sessions) / 60, 2)
        avg_score = round(sum(s.average_score for s in sessions) / len(sessions), 2) if sessions else 0
        counts = Counter(m.classification for m in metrics)
        total = max(1, len(metrics))
        return SessionStats(
            total_sessions=len(sessions),
            total_minutes=total_minutes,
            average_score=avg_score,
            good_percentage=round((counts.get("GOOD POSTURE", 0) / total) * 100, 1),
            slight_percentage=round((counts.get("SLIGHT SLOUCH", 0) / total) * 100, 1),
            bad_percentage=round((counts.get("BAD POSTURE", 0) / total) * 100, 1),
        )

    def _get(self, user: User, session_id: str) -> PostureSession:
        session = self.sessions.get_for_user(session_id, user.id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        return session
