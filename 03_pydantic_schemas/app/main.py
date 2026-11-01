from contextlib import asynccontextmanager
import json
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.config import ROOT
from app.database import engine
from app.api.routes import router


@asynccontextmanager
async def lifespan(app):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield


app = FastAPI(title="Учёт олимпиад — этап 3", docs_url=None, redoc_url=None, lifespan=lifespan)
app.include_router(router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")


@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql"}


@app.get("/docs", include_in_schema=False)
def docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API", swagger_js_url="/static/swagger-ui-bundle.js",
                              swagger_css_url="/static/swagger-ui.css", swagger_favicon_url="data:,")


@app.get("/redoc", include_in_schema=False)
def redoc():
    return get_redoc_html(openapi_url="/openapi.json", title="API", redoc_js_url="/static/redoc.standalone.js",
                          redoc_favicon_url="data:,", with_google_fonts=False)


@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    body = json.dumps(jsonable_encoder({"detail": error.errors()}), ensure_ascii=True)
    return Response(body, status_code=422, media_type="application/json")
