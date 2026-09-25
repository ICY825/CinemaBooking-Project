from app.schemas.common import ORMModel


class CinemaOut(ORMModel):
    id: int
    name: str
    city: str
    address: str
    phone: str | None
