"""Demo data for local development: `python -m app.seed` (safe to run more than once).

The large dataset (>= 2,000 rows) required by task 2.4 will extend this module.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Auditorium, Cinema, Genre, Movie, Seat, User
from app.models.enums import AgeRating, SeatType, UserRole

DEMO_PASSWORD = "Cinema@123"

MOVIES = [
    ("Đào, Phở và Piano", 100, AgeRating.T13, ["Lịch sử", "Chiến tranh"]),
    ("Dune: Part Two", 166, AgeRating.T13, ["Khoa học viễn tưởng", "Phiêu lưu"]),
    ("Kung Fu Panda 4", 94, AgeRating.P, ["Hoạt hình", "Hài"]),
    ("Mai", 131, AgeRating.T18, ["Tâm lý", "Tình cảm"]),
]


def seat_template(rows: str, cols: int, vip_rows: str, couple_row: str | None) -> list[Seat]:
    """Standard seats in front, VIP in the middle rows, couple seats (half as many) in the last row."""
    seats = []
    for row in rows:
        if row == couple_row:
            seats += [Seat(row_label=row, col_number=c, seat_type=SeatType.COUPLE) for c in range(1, cols // 2 + 1)]
        else:
            kind = SeatType.VIP if row in vip_rows else SeatType.STANDARD
            seats += [Seat(row_label=row, col_number=c, seat_type=kind) for c in range(1, cols + 1)]
    return seats


def get_or_create(db: Session, model, defaults: dict | None = None, **lookup):
    obj = db.scalar(select(model).filter_by(**lookup))
    if obj is None:
        obj = model(**lookup, **(defaults or {}))
        db.add(obj)
        db.flush()
    return obj


def run(db: Session) -> None:
    cinema = get_or_create(
        db, Cinema, name="Cinema Cầu Giấy", defaults={"city": "Hà Nội", "address": "241 Xuân Thủy, Cầu Giấy"}
    )
    for name, rows, cols, vip, couple in [("Phòng 1", "ABCDEFGH", 12, "DEF", "H"), ("Phòng 2", "ABCDEF", 10, "CD", None)]:
        room = get_or_create(db, Auditorium, cinema_id=cinema.id, name=name)
        if not room.seats:
            room.seats = seat_template(rows, cols, vip, couple)

    for email, role, full_name in [
        ("admin@cinema.example.com", UserRole.ADMIN, "Quản trị viên"),
        ("staff@cinema.example.com", UserRole.STAFF, "Nhân viên quầy"),
        ("customer@cinema.example.com", UserRole.CUSTOMER, "Khách hàng demo"),
    ]:
        get_or_create(
            db,
            User,
            email=email,
            defaults={
                "password_hash": hash_password(DEMO_PASSWORD),
                "full_name": full_name,
                "role": role,
                "cinema_id": cinema.id if role == UserRole.STAFF else None,
            },
        )

    for title, minutes, age, genre_names in MOVIES:
        movie = get_or_create(
            db, Movie, title=title, defaults={"duration_minutes": minutes, "age_rating": age, "release_date": date(2026, 9, 1)}
        )
        if not movie.genres:
            movie.genres = [get_or_create(db, Genre, name=g) for g in genre_names]

    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        run(session)
    print(f"Seed xong. Tài khoản demo: admin|staff|customer@cinema.example.com / {DEMO_PASSWORD}")
