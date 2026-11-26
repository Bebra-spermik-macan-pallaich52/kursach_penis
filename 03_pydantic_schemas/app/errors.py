import json
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


def register_handlers(app):
    try:
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException
        from starlette.responses import Response
        from psycopg import DataError, IntegrityError, OperationalError
        from psycopg.errors import CheckViolation

        def response(detail, status, headers=None):
            try:
                return Response(
                    json.dumps({"detail": detail}, ensure_ascii=True),
                    status_code=status,
                    media_type="application/json",
                    headers=headers,
                )
            except Exception as error:
                log_error(error, "response")
                raise

        @app.exception_handler(HTTPException)
        async def http_error(request, error):
            try:
                return response(error.detail, error.status_code, error.headers)
            except Exception as failure:
                log_error(failure, "http_error")
                raise

        @app.exception_handler(RequestValidationError)
        async def validation_error(request, error):
            try:
                details = [
                    {"loc": item["loc"], "msg": item["msg"], "type": item["type"]}
                    for item in error.errors()
                ]
                return response(details, 422)
            except Exception as failure:
                log_error(failure, "validation_error")
                raise

        @app.exception_handler(IntegrityError)
        async def integrity_error(request, error):
            try:
                return response(
                    "Данные нарушают ограничения базы",
                    422 if isinstance(error, CheckViolation) else 409,
                )
            except Exception as failure:
                log_error(failure, "integrity_error")
                raise

        @app.exception_handler(DataError)
        async def data_error(request, error):
            try:
                return response("Проверьте формат и длину данных", 422)
            except Exception as failure:
                log_error(failure, "data_error")
                raise

        @app.exception_handler(OperationalError)
        async def database_error(request, error):
            try:
                log_error(error, "database_error")
                return response("База данных временно недоступна", 503)
            except Exception as failure:
                log_error(failure, "database_error")
                raise

        @app.exception_handler(Exception)
        async def unexpected_error(request, error):
            try:
                log_error(error, "unexpected_error")
                return response("Не удалось выполнить операцию", 500)
            except Exception as failure:
                log_error(failure, "unexpected_error")
                raise

    except Exception as error:
        log_error(error, "register_handlers")
        raise
