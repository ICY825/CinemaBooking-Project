from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, VersionMixin
from app.models.enums import (
    PaymentProvider,
    PaymentStatus,
    ReservationStatus,
    SalesChannel,
    TicketStatus,
    db_enum,
)
from app.models.showtime import Money


class Reservation(Base, TimestampMixin, VersionMixin):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)  # null = walk-in
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # staff at the counter
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"), index=True)
    channel: Mapped[SalesChannel] = mapped_column(db_enum(SalesChannel), default=SalesChannel.ONLINE)
    status: Mapped[ReservationStatus] = mapped_column(
        db_enum(ReservationStatus), default=ReservationStatus.PENDING, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    subtotal: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    discount: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="reservation")
    payments: Mapped[list["Payment"]] = relationship(back_populates="reservation")


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), index=True)
    showtime_seat_id: Mapped[int] = mapped_column(ForeignKey("showtime_seats.id"))
    code: Mapped[str] = mapped_column(String(64), unique=True)  # random token encoded in the QR
    price: Mapped[Decimal] = mapped_column(Money)
    status: Mapped[TicketStatus] = mapped_column(db_enum(TicketStatus), default=TicketStatus.VALID)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checked_in_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    reservation: Mapped[Reservation] = relationship(back_populates="tickets")


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), unique=True)
    number: Mapped[str] = mapped_column(String(30), unique=True)
    subtotal: Mapped[Decimal] = mapped_column(Money)
    discount: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    vat: Mapped[Decimal] = mapped_column(Money, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Money)
    pdf_path: Mapped[str | None] = mapped_column(String(500))


class Payment(Base, TimestampMixin, VersionMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), index=True)
    provider: Mapped[PaymentProvider] = mapped_column(db_enum(PaymentProvider))
    amount: Mapped[Decimal] = mapped_column(Money)
    status: Mapped[PaymentStatus] = mapped_column(db_enum(PaymentStatus), default=PaymentStatus.PENDING)
    provider_txn_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reservation: Mapped[Reservation] = relationship(back_populates="payments")
