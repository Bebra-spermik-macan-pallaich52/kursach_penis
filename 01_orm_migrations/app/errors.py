import logging

logger = logging.getLogger("coursework")


def log_error(error, function):
    try:
        if not isinstance(error, (ValueError, TypeError)) and (
            not getattr(error, "status_code", None)
        ):
            logger.error("%s: %s", function, type(error).__name__)
    except Exception:
        return
