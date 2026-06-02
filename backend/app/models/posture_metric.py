from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PostureMetric(Base):
    __tablename__ = "posture_metrics"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_posture_metrics_score_range"),
        Index("ix_posture_metrics_session_captured", "session_id", "captured_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    ratio: Mapped[float | None] = mapped_column(Float)
    distance: Mapped[float | None] = mapped_column(Float)
    angle: Mapped[float | None] = mapped_column(Float)
    alert: Mapped[str | None] = mapped_column(String(255))

    session = relationship("Session", back_populates="metrics")
