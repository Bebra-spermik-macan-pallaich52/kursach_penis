from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import inspect, text
from app.database import engine


with engine.connect() as connection:
    tables = set(inspect(engine).get_table_names())
    assert {"users", "olympiads", "participations", "attachments", "schema_migrations"} <= tables
    for name in ("users", "olympiads", "participations", "attachments"):
        count = connection.execute(text(f"SELECT count(*) FROM {name}")).scalar_one()
        print(name, count)
    inspector = inspect(engine)
    assert inspector.get_foreign_keys("olympiads")[0]["referred_table"] == "users"
    assert len(inspector.get_foreign_keys("participations")) == 2
    assert inspector.get_foreign_keys("attachments")[0]["referred_table"] == "olympiads"
    assert "unique_enrollment" in {item["name"] for item in inspector.get_unique_constraints("participations")}
    assert connection.execute(text("SELECT version FROM schema_migrations")).scalars().all() == ["001_initial"]
print("Таблицы, связи миграции и версия найдены")
