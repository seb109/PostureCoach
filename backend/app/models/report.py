from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_reports_session_id"),
        Index("ix_reports_user_generated", "user_id", "generated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)

    user = relationship("User", back_populates="reports")
    session = relationship("Session", back_populates="report")
