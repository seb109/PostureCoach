from __future__ import annotations

from collections import Counter

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Report, User
from app.repositories import ReportRepository, SessionRepository


class ReportDbService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.reports = ReportRepository(db)
        self.sessions = SessionRepository(db)

    def list(self, user: User) -> list[Report]:
        return self.reports.list_for_user(user.id)

    def get(self, user: User, report_id: str) -> Report:
        report = self.reports.get_for_user(report_id, user.id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        return report

    def generate(self, user: User, session_id: str) -> Report:
        session = self.sessions.get_for_user(session_id, user.id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        metrics = list(session.metrics)
        counts = Counter(m.classification for m in metrics)
        total = max(1, len(metrics))
        summary = {
            "duration_seconds": session.duration_seconds,
            "average_score": session.average_score,
            "total_metrics": len(metrics),
            "good_percentage": round((counts.get("GOOD POSTURE", 0) / total) * 100, 1),
            "slight_percentage": round((counts.get("SLIGHT SLOUCH", 0) / total) * 100, 1),
            "bad_percentage": round((counts.get("BAD POSTURE", 0) / total) * 100, 1),
            "recommendations": _recommendations(session.average_score, counts),
        }
        report = self.reports.upsert(user_id=user.id, session_id=session.id, summary=summary)
        self.db.commit()
        self.db.refresh(report)
        return report

    def as_read_dict(self, report: Report) -> dict:
        return {
            "id": report.id,
            "session_id": report.session_id,
            "generated_at": report.generated_at,
            "summary": report.summary,
            "file_path": report.file_path,
            "download_url": f"/api/v1/reports/{report.id}/download",
        }


def _recommendations(score: float, counts: Counter) -> list[str]:
    tips = []
    if score < 70 or counts.get("BAD POSTURE", 0) > 0:
        tips.append("Raise the screen to eye level and reset shoulders every 20 minutes.")
    if counts.get("SLIGHT SLOUCH", 0) > counts.get("GOOD POSTURE", 0):
        tips.append("Move the chair closer to the desk to reduce forward head drift.")
    if not tips:
        tips.append("Maintain the current setup and keep taking brief movement breaks.")
    return tips
