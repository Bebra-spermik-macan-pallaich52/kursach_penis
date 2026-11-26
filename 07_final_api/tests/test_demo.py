from docx import Document
from app import init_db
from app.database import connect
from app.runtime import run
from app.security import verify_password


def test_demo_records_and_repeat(db, tmp_path, monkeypatch):
    """Учебные данные и документы созданы в нужном количестве и не дублируются."""
    monkeypatch.setattr(init_db, "STORAGE", tmp_path)
    async def fill():
        async with await connect() as connection:
            await init_db.seed_demo(connection)
    run(fill())
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
    run(fill())
    assert [db.execute("SELECT count(*) AS total FROM " + table).fetchone()["total"] for table in tables] == expected
    assert {path.name for path in tmp_path.iterdir()} == names
