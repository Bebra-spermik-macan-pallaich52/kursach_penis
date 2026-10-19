"""Каждый тест работает в откатываемой транзакции отдельной PostgreSQL БД."""
from datetime import date
import os
from pathlib import Path
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
test_url = os.environ["TEST_DATABASE_URL"]
if not make_url(test_url).database.endswith("_test"):
    raise RuntimeError("Тесты разрешены только в отдельной БД с суффиксом _test")
os.environ["DATABASE_URL"] = test_url

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.olympiad import Olympiad
from app.security import hash_password, create_token


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(test_url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine):
    with test_engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, expire_on_commit=False,
                     join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()


@pytest.fixture
def client(db, tmp_path, monkeypatch):
    import app.api.attachments as files
    monkeypatch.setattr(files, "STORAGE", tmp_path)
    def override_db():
        yield db
    applications = [app] + [route.app for route in app.routes if hasattr(route, "app") and isinstance(route.app, type(app))]
    for application in applications:
        application.dependency_overrides[get_db] = override_db
    with TestClient(app) as api:
        yield api
    for application in applications:
        application.dependency_overrides.clear()


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
        db.add(item)
        db.flush()
        users[username] = item
    db.commit()
    return users


@pytest.fixture
def headers(accounts):
    return {name: {"Authorization": "Bearer " + create_token(user)} for name, user in accounts.items()}


@pytest.fixture
def olympiad(db, accounts):
    item = Olympiad(title="Олимпиада Python", description="Учебная олимпиада",
                    teacher_id=accounts["teacher"].id, start_date=date.today(), end_date=date.today())
    db.add(item)
    db.commit()
    return item

