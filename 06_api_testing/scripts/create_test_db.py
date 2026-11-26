from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.errors import log_error
import os
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from dotenv import load_dotenv
from app.runtime import run


async def main():
    try:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        url = os.environ["TEST_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
        options = conninfo_to_dict(url)
        name = options.get("dbname", "")
        if not name.endswith("_test"):
            raise ValueError("Имя тестовой БД должно оканчиваться на _test")
        async with await psycopg.AsyncConnection.connect(
            **{**options, "dbname": "postgres"}, autocommit=True
        ) as db:
            cursor = await db.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
            if not await cursor.fetchone():
                try:
                    await db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
                except psycopg.errors.InsufficientPrivilege:
                    raise RuntimeError(
                        "Создайте тестовую БД по scripts/setup_database.sql от администратора"
                    )
                print("Создана тестовая БД", name)
            else:
                print("Тестовая БД уже существует")
        async with await psycopg.AsyncConnection.connect(url) as db:
            await db.execute("SELECT 1")
            print("Подключение к тестовой БД проверено")
    except Exception as error:
        log_error(error, "main")
        raise


if __name__ == "__main__":
    run(main())
