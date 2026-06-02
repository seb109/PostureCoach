from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
