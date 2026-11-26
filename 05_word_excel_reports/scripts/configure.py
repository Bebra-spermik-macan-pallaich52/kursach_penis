from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.errors import log_error
import secrets


def main():
    try:
        root = Path(__file__).resolve().parents[1]
        target = root / ".env"
        if target.exists():
            print(".env уже существует, настройки сохранены")
            return
        text = (root / ".env.example").read_text(encoding="utf-8")
        text = text.replace("GENERATE_WITH_CONFIGURE_SCRIPT", secrets.token_hex(32))
        target.write_text(text, encoding="utf-8")
        target.chmod(384)
        print("Создан .env со случайным JWT_SECRET")
    except Exception as error:
        log_error(error, "main")
        raise


if __name__ == "__main__":
    main()
