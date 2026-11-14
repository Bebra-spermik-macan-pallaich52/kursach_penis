import psycopg
from psycopg.rows import dict_row
from app.config import DATABASE_URL


def connect(url=None, **options):
    url = (url or DATABASE_URL).replace("postgresql+psycopg://", "postgresql://", 1)
    if not url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("Укажите адрес PostgreSQL в .env")
    return psycopg.connect(url, row_factory=dict_row, **options)


def get_db():
    with connect() as db:
        yield db


def execute(db, query, values=()):
    try:
        return db.execute(query, values)
    except psycopg.Error:
        db.rollback()
        raise
