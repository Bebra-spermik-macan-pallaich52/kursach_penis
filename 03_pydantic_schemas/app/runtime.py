import asyncio
import sys
from app.errors import log_error


def run(coroutine):
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        return asyncio.run(coroutine)
    except Exception as error:
        log_error(error, "run")
        raise
