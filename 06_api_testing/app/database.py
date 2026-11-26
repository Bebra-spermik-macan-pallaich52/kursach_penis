import psycopg
from psycopg.rows import dict_row
from app.config import DATABASE_URL
from app.errors import log_error


async def connect(url=None, **options):
    try:
        url = (url or DATABASE_URL).replace("postgresql+psycopg://", "postgresql://", 1)
        if not url.startswith(("postgresql://", "postgres://")):
            raise ValueError("Укажите адрес PostgreSQL в .env")
        return await psycopg.AsyncConnection.connect(url, row_factory=dict_row, **options)
    except Exception as error:
        log_error(error, "connect")
        raise


async def get_db():
    try:
        async with await connect() as db:
            yield db
    except Exception as error:
        log_error(error, "get_db")
        raise


async def execute(db, query, values=()):
    try:
        return await db.execute(query, values)
    except psycopg.Error:
        await db.rollback()
        raise
    except Exception as error:
        log_error(error, "execute")
        raise


async def fetch_one(db, query, values=()):
    try:
        cursor = await execute(db, query, values)
        return await cursor.fetchone()
    except Exception as error:
        log_error(error, "fetch_one")
        raise


async def fetch_all(db, query, values=()):
    try:
        cursor = await execute(db, query, values)
        return await cursor.fetchall()
    except Exception as error:
        log_error(error, "fetch_all")
        raise
