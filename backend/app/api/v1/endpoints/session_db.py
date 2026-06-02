from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import PostureMetricCreate, PostureMetricRead, SessionRead, SessionStartResponse, SessionStats, SessionStopResponse
from app.services.report_db_service import ReportDbService
from app.services.session_db_service import SessionDbService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionStartResponse)
def start_session(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SessionStartResponse:
    return SessionStartResponse(session=SessionDbService(db).start(current_user))


@router.post("/{session_id}/stop", response_model=SessionStopResponse)
def stop_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SessionStopResponse:
    service = SessionDbService(db)
    session = service.stop(current_user, session_id)
    report = ReportDbService(db).generate(current_user, session.id)
    return SessionStopResponse(session=session, report_id=report.id)


@router.get("", response_model=list[SessionRead])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    return SessionDbService(db).list(current_user)


@router.get("/stats", response_model=SessionStats)
def session_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SessionStats:
    return SessionDbService(db).stats(current_user)


@router.post("/metrics", response_model=PostureMetricRead)
def record_metric(payload: PostureMetricCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return SessionDbService(db).record_metric(current_user, payload)


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return SessionDbService(db).get(current_user, session_id)
