from pathlib import Path
from sqlalchemy import text
from app.database import engine


def migrate():
    folder = Path(__file__).resolve().parents[1] / "migrations"
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version varchar(50) PRIMARY KEY)"))
        versions = set(connection.execute(text("SELECT version FROM schema_migrations")).scalars())
        for path in sorted(folder.glob("*.sql")):
            if path.stem in versions:
                continue
            connection.exec_driver_sql(path.read_text(encoding="utf-8"))
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (:version)"), {"version": path.stem})
            print("Применена миграция:", path.stem)
    print("Структура БД актуальна")


if __name__ == "__main__":
    migrate()
