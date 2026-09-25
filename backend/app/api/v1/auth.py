from datetime import timedelta

import jwt
from fastapi import APIRouter, BackgroundTasks, Request, status
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.core.errors import ApiError, unauthorized
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import ForgotPasswordIn, LoginIn, RefreshIn, RegisterIn, ResetPasswordIn, TokenPair
from app.schemas.user import UserOut
from app.services import audit
from app.services.mailer import send_email

router = APIRouter(prefix="/auth", tags=["auth"])


def issue_tokens(user: User) -> TokenPair:
    access = timedelta(minutes=settings.access_token_minutes)
    return TokenPair(
        access_token=create_token(user.id, "access", user.token_version, access, role=user.role.value),
        refresh_token=create_token(
            user.id, "refresh", user.token_version, timedelta(days=settings.refresh_token_days)
        ),
        expires_in=int(access.total_seconds()),
    )


def find_by_email(db, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: DbSession):
    if find_by_email(db, body.email):
        raise ApiError(409, "EMAIL_TAKEN", "Email đã được sử dụng")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
    )
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=TokenPair)
def login(body: LoginIn, db: DbSession):
    user = find_by_email(db, body.email)
    password_ok = verify_password(body.password, user.password_hash if user else None)
    if user is None or not password_ok:
        raise ApiError(401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng")
    if not user.is_active:
        raise ApiError(403, "ACCOUNT_DISABLED", "Tài khoản đã bị khoá")
    return issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn, db: DbSession):
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except jwt.PyJWTError:
        raise unauthorized()
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active or user.token_version != payload.get("ver"):
        raise unauthorized()
    return issue_tokens(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, db: DbSession):
    """Revokes every access/refresh token of this user (all devices)."""
    user.token_version += 1
    db.commit()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(body: ForgotPasswordIn, db: DbSession, background: BackgroundTasks):
    # Same response whether the email exists or not, so it cannot be used to discover accounts.
    user = find_by_email(db, body.email)
    if user and user.is_active:
        token = create_token(
            user.id, "reset", user.token_version, timedelta(minutes=settings.reset_token_minutes)
        )
        link = f"{settings.frontend_url}/#!/reset-password?token={token}"
        background.add_task(
            send_email,
            user.email,
            "Đặt lại mật khẩu - Cinema Booking",
            f"Chào {user.full_name},\n\nMở liên kết sau để đặt lại mật khẩu "
            f"(hiệu lực {settings.reset_token_minutes} phút):\n{link}\n\n"
            "Nếu bạn không yêu cầu, hãy bỏ qua email này.",
        )
    return {"message": "Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi"}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(body: ResetPasswordIn, db: DbSession, request: Request):
    invalid = ApiError(400, "INVALID_RESET_TOKEN", "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn")
    try:
        payload = decode_token(body.token, "reset")
    except jwt.PyJWTError:
        raise invalid
    user = db.get(User, int(payload["sub"]))
    # token_version is bumped below, so a reset link works only once.
    if user is None or not user.is_active or user.token_version != payload.get("ver"):
        raise invalid
    user.password_hash = hash_password(body.new_password)
    user.token_version += 1
    audit.record(db, actor=user, action="user.reset_password", entity=user, request=request)
    db.commit()
