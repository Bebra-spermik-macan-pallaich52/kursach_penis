from pathlib import Path
import os
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
url = os.environ["TEST_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
options = conninfo_to_dict(url)
name = options.get("dbname", "")
if not name.endswith("_test"):
    raise RuntimeError("Имя тестовой БД должно оканчиваться на _test")
with psycopg.connect(**{**options, "dbname": "postgres"}, autocommit=True) as db:
    if not db.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
        try:
            db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        except psycopg.errors.InsufficientPrivilege:
            raise SystemExit("Создайте тестовую БД по scripts/setup_database.sql от администратора")
        print("Создана тестовая БД", name)
    else:
        print("Тестовая БД уже существует")
with psycopg.connect(url) as db:
    db.execute("SELECT 1")
    print("Подключение к тестовой БД проверено")
