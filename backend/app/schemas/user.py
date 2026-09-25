from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel, Password, Phone


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    cinema_id: int | None
    loyalty_points: int
    row_version: int
    created_at: datetime | None


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=120)
    phone: Phone | None = None
    row_version: int  # optimistic lock: the version the client last saw


class UserCreate(BaseModel):
    email: EmailStr
    password: Password
    full_name: str = Field(min_length=2, max_length=120)
    phone: Phone | None = None
    role: UserRole = UserRole.STAFF
    cinema_id: int | None = None


class UserAdminUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=120)
    phone: Phone | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    cinema_id: int | None = None
    row_version: int
