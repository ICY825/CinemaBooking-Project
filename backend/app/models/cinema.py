from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import SeatType, db_enum


class Cinema(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cinemas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    city: Mapped[str] = mapped_column(String(60), index=True)
    address: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))

    auditoriums: Mapped[list["Auditorium"]] = relationship(back_populates="cinema")


class Auditorium(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "auditoriums"
    __table_args__ = (UniqueConstraint("cinema_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cinema_id: Mapped[int] = mapped_column(ForeignKey("cinemas.id"), index=True)
    name: Mapped[str] = mapped_column(String(60))
    # Buffer between two showtimes in this room (cleaning), used by the overlap check.
    cleaning_minutes: Mapped[int] = mapped_column(Integer, default=15)

    cinema: Mapped[Cinema] = relationship(back_populates="auditoriums")
    seats: Mapped[list["Seat"]] = relationship(
        back_populates="auditorium", order_by="(Seat.row_label, Seat.col_number)"
    )


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("auditorium_id", "row_label", "col_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    auditorium_id: Mapped[int] = mapped_column(ForeignKey("auditoriums.id", ondelete="CASCADE"), index=True)
    row_label: Mapped[str] = mapped_column(String(3))
    col_number: Mapped[int] = mapped_column(Integer)
    seat_type: Mapped[SeatType] = mapped_column(db_enum(SeatType), default=SeatType.STANDARD)
    is_active: Mapped[bool] = mapped_column(default=True)

    auditorium: Mapped[Auditorium] = relationship(back_populates="seats")
