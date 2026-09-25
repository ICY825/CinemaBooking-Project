"""Import every model so Base.metadata is complete (Alembic autogenerate, create_all in tests)."""

from app.models.audit import AuditLog
from app.models.booking import Invoice, Payment, Reservation, Ticket
from app.models.cinema import Auditorium, Cinema, Seat
from app.models.movie import Genre, Movie, movie_genres
from app.models.showtime import Holiday, PriceRule, Showtime, ShowtimeSeat
from app.models.user import User

__all__ = [
    "AuditLog", "Auditorium", "Cinema", "Genre", "Holiday", "Invoice", "Movie", "Payment",
    "PriceRule", "Reservation", "Seat", "Showtime", "ShowtimeSeat", "Ticket", "User", "movie_genres",
]
