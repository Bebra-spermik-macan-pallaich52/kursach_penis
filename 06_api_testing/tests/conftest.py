from datetime import date
import os
from pathlib import Path
import pytest
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict
from fastapi.testclient import TestClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
test_url = os.environ["TEST_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
if not conninfo_to_dict(test_url).get("dbname", "").endswith("_test"):
    raise RuntimeError("Тесты разрешены только в отдельной БД с суффиксом _test")
os.environ["DATABASE_URL"] = test_url

from app.main import app
from app.database import connect
from app.migrate import migrate
from app.models.user import User
from app.models.olympiad import Olympiad
from app.records import insert_user, insert_olympiad
from app.security import hash_password
from app.create_token import create_token


@pytest.fixture(scope="session", autouse=True)
def test_database():
    migrate()


@pytest.fixture
def db(test_database):
    with connect(test_url, autocommit=True) as connection:
        connection.execute("TRUNCATE attachments, participations, olympiads, users RESTART IDENTITY CASCADE")
        yield connection
        connection.execute("TRUNCATE attachments, participations, olympiads, users RESTART IDENTITY CASCADE")


@pytest.fixture
def client(db, tmp_path, monkeypatch):
    import app.api.attachments as files
    monkeypatch.setattr(files, "STORAGE", tmp_path)
    with TestClient(app) as api:
        yield api


@pytest.fixture(scope="session")
def password_hash():
    return hash_password("TestPass2026!")


@pytest.fixture
def accounts(db, password_hash):
    users = {}
    for role, username in [("admin", "admin"), ("teacher", "teacher"),
                            ("teacher", "other_teacher"), ("student", "student"),
                            ("student", "other_student")]:
        item = User(username=username, password_hash=password_hash, role=role,
                    full_name=username + " Тестовый Пользователь", email=username + "@example.org",
                    birth_date=date(2006, 1, 1), institution="Колледж", education_level="СПО",
                    course=3, specialty="Информационные системы")
        insert_user(db, item)
        users[username] = item
    return users


@pytest.fixture
def headers(accounts):
    return {name: {"Authorization": "Bearer " + create_token(user)} for name, user in accounts.items()}


@pytest.fixture
def olympiad(db, accounts):
    item = Olympiad(title="Олимпиада Python", description="Учебная олимпиада",
                    teacher_id=accounts["teacher"].id, start_date=date.today(), end_date=date.today())
    return insert_olympiad(db, item)
