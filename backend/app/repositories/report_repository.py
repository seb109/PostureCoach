from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Report


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: str) -> list[Report]:
        return list(self.db.scalars(select(Report).options(selectinload(Report.session)).where(Report.user_id == user_id).order_by(Report.generated_at.desc())))

    def get_for_user(self, report_id: str, user_id: str) -> Report | None:
        return self.db.scalar(select(Report).options(selectinload(Report.session)).where(Report.id == report_id, Report.user_id == user_id))

    def get_by_session(self, session_id: str, user_id: str) -> Report | None:
        return self.db.scalar(select(Report).where(Report.session_id == session_id, Report.user_id == user_id))

    def upsert(self, user_id: str, session_id: str, summary: dict, file_path: str | None = None) -> Report:
        report = self.get_by_session(session_id, user_id)
        if report is None:
            report = Report(user_id=user_id, session_id=session_id, summary=summary, file_path=file_path)
            self.db.add(report)
        else:
            report.summary = summary
            report.file_path = file_path
        self.db.flush()
        return report
