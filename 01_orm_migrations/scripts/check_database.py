from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.errors import log_error
from app.database import connect
from app.database import fetch_one, fetch_all
from app.runtime import run


async def main():
    try:
        async with await connect() as db:
            tables = {
                row["tablename"]
                for row in await fetch_all(
                    db, "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
            }
            assert {
                "users",
                "olympiads",
                "participations",
                "attachments",
                "schema_migrations",
            } <= tables
            for name in ("users", "olympiads", "participations", "attachments"):
                print(name, (await fetch_one(db, "SELECT count(*) AS total FROM " + name))["total"])
            rows = await fetch_all(
                db,
                """
                    SELECT conrelid::regclass::text AS source, confrelid::regclass::text AS target
                    FROM pg_constraint WHERE contype = 'f'
                """,
            )
            links = {(row["source"], row["target"]) for row in rows}
            assert {
                ("olympiads", "users"),
                ("participations", "users"),
                ("participations", "olympiads"),
                ("attachments", "olympiads"),
            } <= links
            assert await fetch_one(
                db, "SELECT 1 FROM pg_constraint WHERE conname = 'unique_enrollment'"
            )
            versions = {
                row["version"]
                for row in await fetch_all(db, "SELECT version FROM schema_migrations")
            }
            assert {"001_initial", "002_validation"} <= versions
        print("Таблицы, связи и миграции проверены")
    except Exception as error:
        log_error(error, "main")
        raise


if __name__ == "__main__":
    run(main())
