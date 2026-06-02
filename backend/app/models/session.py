from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="ck_sessions_duration_non_negative"),
        CheckConstraint("average_score >= 0 AND average_score <= 100", name="ck_sessions_average_score_range"),
        Index("ix_sessions_user_started", "user_id", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)

    user = relationship("User", back_populates="sessions")
    metrics = relationship("PostureMetric", back_populates="session", cascade="all, delete-orphan", order_by="PostureMetric.captured_at")
    report = relationship("Report", back_populates="session", cascade="all, delete-orphan", uselist=False)

    @property
    def report_id(self) -> str | None:
        return self.report.id if self.report else None
