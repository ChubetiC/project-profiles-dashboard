from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.user_repository import create_user, get_user_by_login


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    expires_in_seconds: int


def register_user(db: Session, login: str, password: str) -> User:
    existing_user = get_user_by_login(db, login)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already exists",
        )

    return create_user(db, login=login, hashed_password=hash_password(password))


def login_user(db: Session, login: str, password: str) -> LoginResult:
    user = get_user_by_login(db, login)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )

    settings = get_settings()
    return LoginResult(
        access_token=create_access_token(subject=user.login),
        expires_in_seconds=settings.access_token_expire_minutes * 60,
    )

