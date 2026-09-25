from datetime import date
from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import AgeRating, db_enum

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)


class Movie(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    age_rating: Mapped[AgeRating] = mapped_column(db_enum(AgeRating), default=AgeRating.P)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))  # review score 0.0-10.0
    language: Mapped[str | None] = mapped_column(String(40))
    director: Mapped[str | None] = mapped_column(String(120))
    release_date: Mapped[date | None] = mapped_column(index=True)
    end_date: Mapped[date | None]
    poster_url: Mapped[str | None] = mapped_column(String(500))
    trailer_url: Mapped[str | None] = mapped_column(String(500))

    genres: Mapped[list[Genre]] = relationship(secondary=movie_genres, lazy="selectin")
