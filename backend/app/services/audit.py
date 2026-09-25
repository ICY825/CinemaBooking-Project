from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models import AuditLog, User

# Never copied into audit_logs.before/after.
_SECRET_FIELDS = {"password_hash", "token_version"}


def snapshot(obj, fields: list[str] | None = None) -> dict:
    """JSON-safe dict of an ORM object's columns (or the given subset), minus secret fields."""
    names = fields or [c.key for c in obj.__mapper__.column_attrs]
    return jsonable_encoder({n: getattr(obj, n) for n in names if n not in _SECRET_FIELDS})


def record(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity,
    before: dict | None = None,
    after: dict | None = None,
    request: Request | None = None,
) -> None:
    """Add an audit row to the current transaction (committed together with the change itself)."""
    db.add(
        AuditLog(
            actor_id=actor.id if actor else None,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=str(entity.id) if entity.id is not None else None,
            before=before,
            after=after,
            ip=request.client.host if request and request.client else None,
        )
    )
