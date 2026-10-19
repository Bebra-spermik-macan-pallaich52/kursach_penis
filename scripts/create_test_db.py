"""Создать отдельную тестовую БД; существующие данные не удаляются."""
from pathlib import Path
import os
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
url = make_url(os.environ["TEST_DATABASE_URL"])
if not url.database.endswith("_test"):
    raise RuntimeError("Имя тестовой БД должно оканчиваться на _test")
with psycopg.connect(host=url.host, port=url.port or 5432, user=url.username,
                     password=url.password, dbname="postgres", autocommit=True) as conn:
    if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (url.database,)).fetchone():
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(url.database)))
        print("Создана тестовая БД", url.database)
    else:
        print("Тестовая БД уже существует")

