from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import DbSession
from app.models import Cinema
from app.schemas.cinema import CinemaOut

router = APIRouter(prefix="/cinemas", tags=["cinemas"])

# Read-only for now (staff assignment, public filters). Full CRUD + seat-map editor: task 2.2.


@router.get("", response_model=list[CinemaOut])
def list_cinemas(db: DbSession, city: str | None = None):
    stmt = select(Cinema).where(Cinema.deleted_at.is_(None))
    if city:
        stmt = stmt.where(Cinema.city == city)
    return db.scalars(stmt.order_by(Cinema.name)).all()
