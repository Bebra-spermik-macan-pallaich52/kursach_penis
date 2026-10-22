"""Обязательный объём демонстрационных данных и повторная инициализация."""
from docx import Document
from app import init_db
from app.models.user import User
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.models.attachment import Attachment
from app.security import verify_password


def test_demo_records_and_repeat(db, tmp_path, monkeypatch):
    monkeypatch.setattr(init_db, "STORAGE", tmp_path)
    init_db.seed_demo(db)
    models = (User, Olympiad, Participation, Attachment)
    expected = [111, 50, 150, 200]
    assert [db.query(model).count() for model in models] == expected
    assert db.query(User).filter_by(role="teacher").count() == 50
    assert db.query(User).filter_by(role="student").count() == 60
    admin = db.query(User).filter_by(username="admin").one()
    assert verify_password("Admin2026!", admin.password_hash)
    assert {item.kind for item in db.query(Attachment)} == {
        "regulation", "task", "certificate", "award"}
    names = {item.stored_name for item in db.query(Attachment)}
    assert len(names) == 200
    for name in names:
        assert Document(tmp_path / name).paragraphs[0].text
    init_db.seed_demo(db)
    assert [db.query(model).count() for model in models] == expected
    assert {path.name for path in tmp_path.iterdir()} == names
