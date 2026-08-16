from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.services.auth_service import login_user, register_user
from app.services.exceptions import InvalidCredentialsError, LoginAlreadyExistsError

router = APIRouter(tags=["auth"])


class UserCreateRequest(BaseModel):
    login: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=72)
    repeat_password: str = Field(min_length=8, max_length=72)

    @model_validator(mode="after")
    def validate_passwords_match(self) -> "UserCreateRequest":
        if self.password != self.repeat_password:
            raise ValueError("password and repeat_password must match")
        return self


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=72)


class UserResponse(BaseModel):
    id: int
    login: str

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(id=user.id, login=user.login)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


@router.post("/auth", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = register_user(db, login=payload.login, password=payload.password)
    except LoginAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Login already exists",
        ) from error

    return UserResponse.from_user(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        result = login_user(db, login=payload.login, password=payload.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        ) from error

    return TokenResponse(
        access_token=result.access_token,
        expires_in_seconds=result.expires_in_seconds,
    )

