import argparse
import asyncio
import sys
import uvicorn
from app.errors import log_error


def main():
    try:
        parser = argparse.ArgumentParser(description="Запуск FastAPI")
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--no-reload", action="store_true")
        args = parser.parse_args()
        if not 1 <= args.port <= 65535:
            raise ValueError("Порт должен быть от 1 до 65535")
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, reload=not args.no_reload)
    except Exception as error:
        log_error(error, "main")
        raise


if __name__ == "__main__":
    main()
