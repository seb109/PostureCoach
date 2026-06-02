from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_profile(self, user: User, full_name: str | None) -> User:
        if full_name is not None:
            user.full_name = full_name
        self.db.commit()
        self.db.refresh(user)
        return user
