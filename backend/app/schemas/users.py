from pydantic import BaseModel, EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}