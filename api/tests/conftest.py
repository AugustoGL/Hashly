import io
import os

# Antes de importar cualquier módulo de la app
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-0123456789")
os.environ["HASHLY_AUTO_MIGRATE"] = "0"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["AUTH_RATE_LIMIT_PER_MINUTE"] = "0"

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.database as database

from database.database import Base, get_db
from database.models import User
from auth.auth import password_hasher, create_access_token


# ============================================================
# Test database
# ============================================================

test_engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


# Reemplazamos el engine de producción antes de importar main.
database.engine = test_engine
database.SessionLocal = TestSessionLocal


from main import app


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def clean_rate_limiter():
    """Cada test arranca con el limitador vacío."""

    from auth import ratelimit

    ratelimit.HITS.clear()
    yield
    ratelimit.HITS.clear()


@pytest.fixture(autouse=True)
def fake_ots(monkeypatch):
    """Los tests nunca tocan la red: el cliente OTS se reemplaza."""

    from ots import client

    monkeypatch.setattr(
        client, "stamp", lambda digest: b"OTS-PENDING:" + digest
    )

    monkeypatch.setattr(
        client,
        "upgrade",
        lambda proof: client.UpgradeResult(
            proof=proof, confirmed=False, block_height=None
        ),
    )


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user(db):

    user = User(
        email="usuario@test.com",
        password_hash=password_hasher.hash(
            "password123"
        )
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def second_user(db):

    user = User(
        email="otro@test.com",
        password_hash=password_hasher.hash(
            "password456"
        )
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def auth_headers(user):

    token = create_access_token(
        user.id
    )

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def second_auth_headers(second_user):

    token = create_access_token(
        second_user.id
    )

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# Helpers
# ============================================================

@pytest.fixture
def text_file():

    def make_file(
        filename="archivo.txt",
        content=b"Contenido de prueba"
    ):

        return (
            "files",
            (
                filename,
                io.BytesIO(content),
                "text/plain"
            )
        )

    return make_file