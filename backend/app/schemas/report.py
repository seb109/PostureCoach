from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    session_id: str


class ReportRead(BaseModel):
    id: str
    session_id: str
    generated_at: datetime
    summary: dict
    file_path: str | None
    download_url: str | None = None

    model_config = {"from_attributes": True}
