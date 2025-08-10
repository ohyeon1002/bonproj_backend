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
    Test client to emulate a signed user.
    """

    app.dependency_overrides[get_db] = lambda: get_test_db

    test_user = get_test_db.exec(select(models.User).where(models.User.id == 1)).one()

    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_optional_current_activate_user] = lambda: test_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def solve_response(signed_client):
    """
    Get a response from /solve to test endpoints in /results.
    """
    response = signed_client.get(
        "/api/solve/",
        params={
            "examtype": "practice",
            "year": "2021",
            "license": "항해사",
            "level": "1",
            "round": "1",
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    odapset_id: int = response_data["odapset_id"]
    gichulqna_id: int = response_data["qnas"][0]["id"]
    answer: str = response_data["qnas"][0]["answer"]
    return odapset_id, gichulqna_id, answer


@pytest.fixture(scope="function")
def save_one_and_get_mypage_response(solve_response, signed_client):
    odapset_id, gichulqna_id, answer = solve_response
    save_one_response = signed_client.post(
        "/api/results/save",
        json={
            "choice": "가",
            "gichulqna_id": gichulqna_id,
            "answer": answer,
            "odapset_id": odapset_id,
        },
    )
    assert save_one_response.status_code == 201
    odaps_response = signed_client.get("/api/mypage/odaps")
    assert odaps_response.status_code == 200
    odaps_response_data = odaps_response.json()
    assert isinstance(odaps_response_data, list)
    required_keys = {
        "id",
        "subject",
        "qnum",
        "questionstr",
        "ex1str",
        "ex2str",
        "ex3str",
        "ex4str",
        "answer",
        "explanation",
        "gichulset",
        "gichulset_id",
        "choice",
        "result_id",
        "hidden",
        "attempt_counts",
    }
    assert required_keys == odaps_response_data[0].keys()
    required_gichulset_keys = {"year", "type", "grade", "inning"}
    assert required_gichulset_keys == odaps_response_data[0]["gichulset"].keys()
    return odaps_response_data[0]["result_id"]


@pytest.fixture(scope="function")
def save_many_and_get_mypage_exam_response(signed_client):
    solve_response = signed_client.get(
        "/api/solve/",
        params={
            "examtype": "exam",
            "year": "2021",
            "license": "항해사",
            "level": "1",
            "round": "1",
        },
    )
    solve_response_data = solve_response.json()
    odapset_id = solve_response_data["odapset_id"]
    savemany_response = signed_client.post(
        "/api/results/savemany",
        json={
            "odapset_id": odapset_id,
            "duration_sec": 3600,
            "results": [
                {"choice": "아", "answer": "아", "gichulqna_id": 1},
                {"choice": "가", "answer": "가", "gichulqna_id": 2},
                {"choice": "나", "answer": "아", "gichulqna_id": 3},
                {"choice": "사", "answer": "나", "gichulqna_id": 4},
                {"choice": "아", "answer": "아", "gichulqna_id": 5},
                {"choice": "가", "answer": "가", "gichulqna_id": 6},
                {"choice": "나", "answer": "나", "gichulqna_id": 7},
                {"choice": "가", "answer": "아", "gichulqna_id": 8},
                {"choice": "아", "answer": "아", "gichulqna_id": 9},
                {"choice": "사", "answer": "가", "gichulqna_id": 10},
            ],
        },
    )
    assert savemany_response.status_code == 201
    return odapset_id


@pytest.fixture(scope="function")
def get_cbt_and_save_many(signed_client):
    solve_response = signed_client.get(
        "/api/cbt/",
        params={"license": "항해사", "level": "1", "subjects": ["항해", "운용"]},
    )
    solve_response_data = solve_response.json()
    odapset_id = solve_response_data["odapset_id"]
    savemany_response = signed_client.post(
        "/api/results/savemany",
        json={
            "odapset_id": odapset_id,
            "duration_sec": 3600,
            "results": [
                {"choice": "아", "answer": "아", "gichulqna_id": 1},
                {"choice": "가", "answer": "가", "gichulqna_id": 2},
                {"choice": "나", "answer": "아", "gichulqna_id": 3},
                {"choice": "사", "answer": "나", "gichulqna_id": 4},
                {"choice": "아", "answer": "아", "gichulqna_id": 5},
                {"choice": "가", "answer": "가", "gichulqna_id": 6},
                {"choice": "나", "answer": "나", "gichulqna_id": 7},
                {"choice": "가", "answer": "아", "gichulqna_id": 8},
                {"choice": "아", "answer": "아", "gichulqna_id": 9},
                {"choice": "사", "answer": "가", "gichulqna_id": 10},
            ],
        },
    )
    assert savemany_response.status_code == 201
    return odapset_id
