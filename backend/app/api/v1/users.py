from typing import Annotated

from fastapi import APIRouter, Query, Request, status
from sqlalchemy import func, or_, select

from app.core.deps import AdminUser, CurrentUser, DbSession
from app.core.errors import ApiError, not_found, version_conflict
from app.core.security import hash_password, verify_password
from app.models import Cinema, User
from app.models.enums import UserRole
from app.schemas.auth import ChangePasswordIn
from app.schemas.common import Page
from app.schemas.user import ProfileUpdate, UserAdminUpdate, UserCreate, UserOut
from app.services import audit

router = APIRouter(prefix="/users", tags=["users"])


NULLABLE_FIELDS = {"phone", "cinema_id"}


def patch_fields(body) -> dict:
    """Fields the client actually sent; an explicit null only clears nullable columns."""
    return {
        k: v
        for k, v in body.model_dump(exclude_unset=True, exclude={"row_version"}).items()
        if v is not None or k in NULLABLE_FIELDS
    }


def check_version(obj, row_version: int) -> None:
    if obj.row_version != row_version:
        raise version_conflict()


def check_staff_cinema(db, role: UserRole, cinema_id: int | None) -> None:
    if role == UserRole.STAFF and cinema_id is None:
        raise ApiError(422, "CINEMA_REQUIRED", "Nhân viên phải thuộc một rạp")
    if cinema_id is not None and db.get(Cinema, cinema_id) is None:
        raise not_found("Rạp")


# ---- Current user ---------------------------------------------------------------------------


@router.get("/me", response_model=UserOut)
def get_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: ProfileUpdate, user: CurrentUser, db: DbSession):
    check_version(user, body.row_version)
    for field, value in patch_fields(body).items():
        setattr(user, field, value)
    db.commit()
    return user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: ChangePasswordIn, user: CurrentUser, db: DbSession, request: Request):
    """Signs out every session, including this one: the client must log in again."""
    if not verify_password(body.current_password, user.password_hash):
        raise ApiError(400, "WRONG_PASSWORD", "Mật khẩu hiện tại không đúng")
    user.password_hash = hash_password(body.new_password)
    user.token_version += 1
    audit.record(db, actor=user, action="user.change_password", entity=user, request=request)
    db.commit()


# ---- Admin: account management --------------------------------------------------------------


@router.get("", response_model=Page[UserOut])
def list_users(
    _: AdminUser,
    db: DbSession,
    q: str | None = None,
    role: UserRole | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    stmt = select(User)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.full_name).like(like)))
    if role:
        stmt = stmt.where(User.role == role)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(User.id).offset((page - 1) * size).limit(size)).all()
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, admin: AdminUser, db: DbSession, request: Request):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise ApiError(409, "EMAIL_TAKEN", "Email đã được sử dụng")
    check_staff_cinema(db, body.role, body.cinema_id)
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
        role=body.role,
        cinema_id=body.cinema_id,
    )
    db.add(user)
    db.flush()
    audit.record(db, actor=admin, action="user.create", entity=user, after=audit.snapshot(user), request=request)
    db.commit()
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, _: AdminUser, db: DbSession):
    user = db.get(User, user_id)
    if user is None:
        raise not_found("Tài khoản")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserAdminUpdate, admin: AdminUser, db: DbSession, request: Request):
    user = db.get(User, user_id)
    if user is None:
        raise not_found("Tài khoản")
    check_version(user, body.row_version)
    changes = patch_fields(body)
    demoted = changes.get("role", UserRole.ADMIN) != UserRole.ADMIN
    if user.id == admin.id and (changes.get("is_active") is False or demoted):
        raise ApiError(400, "SELF_LOCKOUT", "Không thể tự khoá hoặc tự hạ quyền tài khoản của mình")

    before = audit.snapshot(user)
    for field, value in changes.items():
        setattr(user, field, value)
    check_staff_cinema(db, user.role, user.cinema_id)
    if "role" in changes or changes.get("is_active") is False:
        user.token_version += 1  # permissions changed: force re-login
    db.flush()
    audit.record(
        db, actor=admin, action="user.update", entity=user, before=before, after=audit.snapshot(user), request=request
    )
    db.commit()
    return user
