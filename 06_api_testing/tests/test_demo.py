from docx import Document
from app import init_db
from app.security import verify_password


def test_demo_records_and_repeat(db, tmp_path, monkeypatch):
    monkeypatch.setattr(init_db, "STORAGE", tmp_path)
    init_db.seed_demo(db)
    tables = ("users", "olympiads", "participations", "attachments")
    expected = [111, 50, 150, 200]
    assert [db.execute("SELECT count(*) AS total FROM " + table).fetchone()["total"] for table in tables] == expected
    assert db.execute("SELECT count(*) AS total FROM users WHERE role = 'teacher'").fetchone()["total"] == 50
    assert db.execute("SELECT count(*) AS total FROM users WHERE role = 'student'").fetchone()["total"] == 60
    admin = db.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
    assert verify_password("Admin2026!", admin["password_hash"])
    assert {row["kind"] for row in db.execute("SELECT kind FROM attachments")} == {
        "regulation", "task", "certificate", "award"}
    names = {row["stored_name"] for row in db.execute("SELECT stored_name FROM attachments")}
    assert len(names) == 200
    for name in names:
        assert Document(tmp_path / name).paragraphs[0].text
    init_db.seed_demo(db)
    assert [db.execute("SELECT count(*) AS total FROM " + table).fetchone()["total"] for table in tables] == expected
    assert {path.name for path in tmp_path.iterdir()} == names
