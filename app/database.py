import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
STORAGE = Path(os.getenv("STORAGE_DIR", str(ROOT / "storage")))


class Base(DeclarativeBase):
    pass


if not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError("Укажите адрес PostgreSQL в DATABASE_URL файла .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
