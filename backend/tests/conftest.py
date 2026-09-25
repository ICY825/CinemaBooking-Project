import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Cinema, User
from app.models.enums import UserRole

PASSWORD = "Passw0rd!"


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    def _make(role: UserRole = UserRole.CUSTOMER, email: str | None = None, **kw) -> User:
        user = User(
            email=email or f"{role.value}{db.query(User).count()}@test.vn",
            password_hash=hash_password(PASSWORD),
            full_name=f"Test {role.value}",
            role=role,
            **kw,
        )
        db.add(user)
        db.commit()
        return user

    return _make


@pytest.fixture
def cinema(db):
    c = Cinema(name="CGV Test", city="Hà Nội", address="1 Test St")
    db.add(c)
    db.commit()
    return c


@pytest.fixture
def login(client):
    def _login(user: User) -> dict:
        res = client.post("/api/v1/auth/login", json={"email": user.email, "password": PASSWORD})
        assert res.status_code == 200, res.text
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    return _login
