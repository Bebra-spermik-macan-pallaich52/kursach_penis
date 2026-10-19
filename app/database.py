from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


if not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError("Укажите DATABASE_URL PostgreSQL в .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db

