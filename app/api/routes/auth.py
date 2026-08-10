from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserCreateRequest, UserResponse
from app.services.auth_service import login_user, register_user

router = APIRouter(tags=["auth"])


@router.post("/auth", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)) -> User:
    return register_user(db, login=payload.login, password=payload.password)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    result = login_user(db, login=payload.login, password=payload.password)
    return TokenResponse(
        access_token=result.access_token,
        expires_in_seconds=result.expires_in_seconds,
    )

