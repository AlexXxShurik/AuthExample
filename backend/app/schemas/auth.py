from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None
    email: EmailStr
    password: str
    password_repeat: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
