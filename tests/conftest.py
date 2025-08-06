import pytest, os, sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel, select
from app import models
from app.core.config import settings
from app.main import app
from app.database import get_db
from app.dependencies import (
    get_optional_current_activate_user,
    get_current_active_user,
)
from scripts.jsonImport import insertData

SQLITE_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})


def dropcreate():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def import_one_json():
    base_path = settings.BASE_PATH
    json_path = base_path / "항해사/D1_2021_01/D1_2021_01.json"
    insertData(engine, json_path)


def add_one_user():
    valid_user = models.User(
        username="pytest@example.com",
        indivname="Ben Davis",
        id=1,
        hashed_password="$2b$12$5kLJtWwYcuDjXirstPNEI.hgP5yWq1aTSIzUB.qUlli8BBXFqHpc.",
    )
    disabled_user = models.User(
        username="disabled@example.com",
        indivname="Brennan Johnson",
        id=2,
        hashed_password="$2b$12$5kLJtWwYcuDjXirstPNEI.hgP5yWq1aTSIzUB.qUlli8BBXFqHpc.",
        disabled=True,
    )
    with Session(engine) as session:
        session.add(valid_user)
        session.add(disabled_user)
        session.commit()


@pytest.fixture(scope="session")
def setup_db():
    dropcreate()
    import_one_json()
    add_one_user()
    yield
    engine.dispose()
    os.remove("./test.db")


@pytest.fixture(scope="function")
def get_test_db(setup_db):
    db = Session(engine)
    yield db
    db.rollback()
    db.close()


@pytest.fixture(scope="function")
def page_client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def client(get_test_db):
    """
    Test client to emulate an unsigned user.
    """

    app.dependency_overrides[get_db] = lambda: get_test_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def signed_client(get_test_db):
    """
    test client to emulate a signed user.
    """

    app.dependency_overrides[get_db] = lambda: get_test_db

    test_user = get_test_db.exec(select(models.User).where(models.User.id == 1)).one()

    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_optional_current_activate_user] = lambda: test_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides = {}
