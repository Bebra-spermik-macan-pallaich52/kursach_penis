from app.errors import log_error
from app.errors import register_handlers
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from app.config import ROOT
from app.database import connect
from app.api import users, olympiads, participations


@asynccontextmanager
async def lifespan(app):
    try:
        async with await connect() as connection:
            await connection.execute("SELECT 1")
        yield
    except Exception as error:
        log_error(error, "lifespan")
        raise


app = FastAPI(title="Учёт олимпиад — этап 2", docs_url=None, redoc_url=None, lifespan=lifespan)
register_handlers(app)
for router in (users.router, olympiads.router, participations.router):
    app.include_router(router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")


@app.get("/health")
async def health():
    try:
        async with await connect() as connection:
            await connection.execute("SELECT 1")
        return {"status": "ok", "database": "postgresql"}
    except Exception as error:
        log_error(error, "health")
        raise


@app.get("/docs", include_in_schema=False)
async def docs():
    try:
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="API",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
            swagger_favicon_url="data:,",
        )
    except Exception as error:
        log_error(error, "docs")
        raise


@app.get("/redoc", include_in_schema=False)
async def redoc():
    try:
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="API",
            redoc_js_url="/static/redoc.standalone.js",
            redoc_favicon_url="data:,",
            with_google_fonts=False,
        )
    except Exception as error:
        log_error(error, "redoc")
        raise
