from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import Password, Phone


class RegisterIn(BaseModel):
    email: EmailStr
    password: Password
    full_name: str = Field(min_length=2, max_length=120)
    phone: Phone | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=200)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until the access token expires


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: Password


class ChangePasswordIn(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: Password
