from app.errors import log_error
from app.database import fetch_all
from app.runtime import run
import asyncio
from pathlib import Path
from app.database import connect


async def migrate():
    try:
        folder = Path(__file__).resolve().parents[1] / "migrations"
        async with await connect() as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version varchar(50) PRIMARY KEY)"
            )
            versions = {
                row["version"]
                for row in await fetch_all(db, "SELECT version FROM schema_migrations")
            }
            for path in sorted(folder.glob("*.sql")):
                if path.stem not in versions:
                    await db.execute(await asyncio.to_thread(path.read_text, encoding="utf-8"))
                    await db.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,)
                    )
                    print("Применена миграция:", path.stem)
        print("Структура БД актуальна")
    except Exception as error:
        log_error(error, "migrate")
        raise


if __name__ == "__main__":
    run(migrate())
