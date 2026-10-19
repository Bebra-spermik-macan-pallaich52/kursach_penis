"""Настройки читаются из .env в корне проекта."""
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
TOKEN_MINUTES = int(os.getenv("TOKEN_MINUTES", "60"))
STORAGE = Path(os.getenv("STORAGE_DIR", str(ROOT / "storage")))
MAX_FILE_SIZE = 5 * 1024 * 1024

