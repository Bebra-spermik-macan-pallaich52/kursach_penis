"""Создание локального .env без перезаписи настроек пользователя."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print(".env уже существует, настройки сохранены")
else:
    text = (root / ".env.example").read_text(encoding="utf-8")
    text = text.replace("GENERATE_WITH_CONFIGURE_SCRIPT", secrets.token_hex(32))
    target.write_text(text, encoding="utf-8")
    target.chmod(0o600)
    print("Создан .env со случайным JWT_SECRET")

