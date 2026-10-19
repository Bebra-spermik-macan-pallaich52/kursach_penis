import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
TIMEOUT = 10

