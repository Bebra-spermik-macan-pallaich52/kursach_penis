from pathlib import Path
from app.database import connect


def migrate():
    folder = Path(__file__).resolve().parents[1] / "migrations"
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version varchar(50) PRIMARY KEY)")
        versions = {row["version"] for row in db.execute("SELECT version FROM schema_migrations")}
        for path in sorted(folder.glob("*.sql")):
            if path.stem not in versions:
                db.execute(path.read_text(encoding="utf-8"))
                db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
                print("Применена миграция:", path.stem)
    print("Структура БД актуальна")


if __name__ == "__main__":
    migrate()
