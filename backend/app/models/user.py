from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, VersionMixin
from app.models.enums import UserRole, db_enum


class User(Base, TimestampMixin, VersionMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole), default=UserRole.CUSTOMER, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    # Staff are scoped to one cinema (POS, check-in). Null for customers/admins.
    cinema_id: Mapped[int | None] = mapped_column(ForeignKey("cinemas.id"))
    # Bumped on logout / password change to revoke every refresh & reset token issued before.
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0)
