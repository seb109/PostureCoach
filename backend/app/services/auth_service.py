from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, generate_refresh_token, hash_password, hash_refresh_token, refresh_expires_at, verify_password
from app.models import User
from app.repositories import TokenRepository, UserRepository
from app.schemas import TokenPair


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)

    def register(self, email: str, full_name: str, password: str) -> TokenPair:
        if self.users.get_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")
        user = self.users.create(email=email, full_name=full_name, hashed_password=hash_password(password))
        pair = self._issue_pair(user)
        self.db.commit()
        return pair

    def login(self, email: str, password: str) -> TokenPair:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled.")
        user.last_login_at = datetime.now(timezone.utc)
        pair = self._issue_pair(user)
        self.db.commit()
        return pair

    def refresh(self, refresh_token: str) -> TokenPair:
        token = self.tokens.get_active(hash_refresh_token(refresh_token))
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
        user = self.users.get(token.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
        self.tokens.revoke(token)
        pair = self._issue_pair(user)
        self.db.commit()
        return pair

    def logout(self, refresh_token: str) -> None:
        token = self.tokens.get_active(hash_refresh_token(refresh_token))
        if token:
            self.tokens.revoke(token)
            self.db.commit()

    def _issue_pair(self, user: User) -> TokenPair:
        refresh = generate_refresh_token()
        self.tokens.create(user_id=user.id, token_hash=hash_refresh_token(refresh), expires_at=refresh_expires_at())
        return TokenPair(access_token=create_access_token(user.id), refresh_token=refresh)
