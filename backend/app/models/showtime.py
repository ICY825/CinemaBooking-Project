from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, VersionMixin
from app.models.enums import DayType, ScreenFormat, SeatType, ShowtimeSeatStatus, ShowtimeStatus, db_enum

Money = Numeric(12, 2)


class Showtime(Base, TimestampMixin, VersionMixin):
    __tablename__ = "showtimes"
    __table_args__ = (Index("ix_showtimes_auditorium_starts", "auditorium_id", "starts_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    auditorium_id: Mapped[int] = mapped_column(ForeignKey("auditoriums.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    format: Mapped[ScreenFormat] = mapped_column(db_enum(ScreenFormat), default=ScreenFormat.F2D)
    base_price: Mapped[Decimal] = mapped_column(Money)
    status: Mapped[ShowtimeStatus] = mapped_column(db_enum(ShowtimeStatus), default=ShowtimeStatus.SCHEDULED)

    movie = relationship("Movie")
    auditorium = relationship("Auditorium")


class PriceRule(Base, TimestampMixin):
    """Surcharge added on top of Showtime.base_price. Null criteria = matches anything."""

    __tablename__ = "price_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    seat_type: Mapped[SeatType | None] = mapped_column(db_enum(SeatType))
    day_type: Mapped[DayType | None] = mapped_column(db_enum(DayType))
    format: Mapped[ScreenFormat | None] = mapped_column(db_enum(ScreenFormat))
    time_from: Mapped[time | None]
    time_to: Mapped[time | None]
    surcharge: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class Holiday(Base):
    __tablename__ = "holidays"

    day: Mapped[date] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))


class ShowtimeSeat(Base, VersionMixin):
    """Seat inventory of one showtime. The UNIQUE(showtime_id, seat_id) row + a conditional UPDATE
    on `status` is what makes double booking impossible (see PLAN.md, section 5.1)."""

    __tablename__ = "showtime_seats"
    __table_args__ = (
        UniqueConstraint("showtime_id", "seat_id"),
        Index("ix_showtime_seats_status_held_until", "status", "held_until"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id", ondelete="CASCADE"))
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id"))
    status: Mapped[ShowtimeSeatStatus] = mapped_column(
        db_enum(ShowtimeSeatStatus), default=ShowtimeSeatStatus.AVAILABLE
    )
    reservation_id: Mapped[int | None] = mapped_column(ForeignKey("reservations.id"), index=True)
    held_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    price: Mapped[Decimal] = mapped_column(Money)  # price snapshot at showtime creation
