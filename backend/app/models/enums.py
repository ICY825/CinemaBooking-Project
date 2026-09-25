import enum

from sqlalchemy import Enum


def db_enum(enum_cls: type[enum.Enum]) -> Enum:
    """Store enums as VARCHAR (portable across Postgres/SQLite, easy to extend without ALTER TYPE)."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=20,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
    ADMIN = "admin"


class SeatType(str, enum.Enum):
    STANDARD = "standard"
    VIP = "vip"
    COUPLE = "couple"


class AgeRating(str, enum.Enum):
    P = "P"
    K = "K"
    T13 = "T13"
    T16 = "T16"
    T18 = "T18"


class ScreenFormat(str, enum.Enum):
    F2D = "2D"
    F3D = "3D"
    IMAX = "IMAX"


class ShowtimeStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class DayType(str, enum.Enum):
    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


class ShowtimeSeatStatus(str, enum.Enum):
    AVAILABLE = "available"
    HELD = "held"
    SOLD = "sold"
    BLOCKED = "blocked"


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class SalesChannel(str, enum.Enum):
    ONLINE = "online"
    COUNTER = "counter"


class TicketStatus(str, enum.Enum):
    VALID = "valid"
    USED = "used"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentProvider(str, enum.Enum):
    VNPAY = "vnpay"
    MOMO = "momo"
    CASH = "cash"
    MOCK = "mock"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
