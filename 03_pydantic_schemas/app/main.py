from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from app.config import ROOT
from app.database import connect
from app.api.routes import router


@asynccontextmanager
async def lifespan(app):
    with connect() as connection:
        connection.execute("SELECT 1")
    yield


app = FastAPI(title="Учёт олимпиад — этап 3", docs_url=None, redoc_url=None, lifespan=lifespan)
app.include_router(router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")


@app.get("/health")
def health():
    with connect() as connection:
        connection.execute("SELECT 1")
    return {"status": "ok", "database": "postgresql"}


@app.get("/docs", include_in_schema=False)
def docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API", swagger_js_url="/static/swagger-ui-bundle.js",
                              swagger_css_url="/static/swagger-ui.css", swagger_favicon_url="data:,")


@app.get("/redoc", include_in_schema=False)
def redoc():
    return get_redoc_html(openapi_url="/openapi.json", title="API", redoc_js_url="/static/redoc.standalone.js",
                          redoc_favicon_url="data:,", with_google_fonts=False)




from fastapi.exceptions import RequestValidationError
import json
from fastapi.responses import JSONResponse, Response
from psycopg import IntegrityError, DataError
from psycopg.errors import CheckViolation


@app.exception_handler(RequestValidationError)
async def invalid_request(request, error):
    errors = [{"loc": item["loc"], "msg": item["msg"], "type": item["type"]} for item in error.errors()]
    return Response(json.dumps({"detail": errors}, ensure_ascii=True), status_code=422, media_type="application/json")


@app.exception_handler(IntegrityError)
async def invalid_record(request, error):
    return JSONResponse({"detail": "Данные нарушают ограничения базы"}, status_code=422 if isinstance(error, CheckViolation) else 409)


@app.exception_handler(DataError)
async def invalid_data(request, error):
    return JSONResponse({"detail": "Проверьте формат и длину данных"}, status_code=422)
