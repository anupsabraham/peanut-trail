"""Shared pytest fixtures for unit and integration tests."""

from collections.abc import Generator
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Transaction, Vendor

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, Any, None]:
    """Create an in-memory SQLite engine for the test session."""
    _engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db(engine: Engine) -> Generator[Session, Any, None]:
    """Provide a database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)  # noqa: N806
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, Any, None]:
    """Provide a FastAPI TestClient with the test DB injected."""

    def override_get_db() -> Generator[Session, Any, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper factories — create ORM objects without worrying about defaults
# ---------------------------------------------------------------------------


def make_vendor(db: Session, name: str) -> Vendor:
    vendor = Vendor(name=name)
    db.add(vendor)
    db.flush()
    return vendor


def make_transaction(db: Session, **kwargs: object) -> Transaction:
    """Create a Transaction with sensible defaults for testing."""
    defaults = {
        "debit_date": date(2026, 6, 1),
        "actual_date": date(2026, 6, 1),
        "narration": "Test narration",
        "txn_number": f"TXN{id(kwargs)}",
        "debit_amount": 100.00,
        "credit_amount": 0.00,
        "category": "Food",
        "sub_category": "Groceries",
        "notes": "",
        "exclude": False,
    }
    defaults.update(kwargs)
    txn = Transaction(**defaults)
    db.add(txn)
    db.flush()
    return txn
