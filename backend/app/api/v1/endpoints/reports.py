from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import ReportGenerateRequest, ReportRead
from app.services.report_db_service import ReportDbService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportRead])
def list_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    service = ReportDbService(db)
    return [service.as_read_dict(report) for report in service.list(current_user)]


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = ReportDbService(db)
    return service.as_read_dict(service.get(current_user, report_id))


@router.post("/generate", response_model=ReportRead)
def generate_report(payload: ReportGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = ReportDbService(db)
    return service.as_read_dict(service.generate(current_user, payload.session_id))


@router.get("/{report_id}/download")
def download_report(report_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    service = ReportDbService(db)
    report = service.get(current_user, report_id)
    content = json.dumps(service.as_read_dict(report), indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="posture-report-{report.id}.json"'},
    )
