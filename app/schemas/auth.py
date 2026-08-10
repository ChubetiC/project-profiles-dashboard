from pydantic import BaseModel, Field, model_validator


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

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int

