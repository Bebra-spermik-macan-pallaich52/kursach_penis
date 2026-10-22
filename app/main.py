"""Главное приложение и две версии REST API."""
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.config import JWT_SECRET, ROOT, STORAGE
from app.database import engine
from app.schemas.error_read import ErrorRead
from app.api import auth, users, olympiads, participations, protocols, attachments

DESCRIPTION = """Учёт участия студентов в олимпиадах и конкурсах профессионального мастерства.

Роли: **student**, **teacher**, **admin**. Гость читает общедоступные данные.
Для входа используйте POST /auth/token (form-data: username, password),
затем кнопку Authorize. Токен передаётся в Authorization: Bearer.
Статусы протокола: draft → prepared → published; prepared → draft.
Ошибки: 401 — нет авторизации; 403 — нет прав; 404 — нет объекта;
409 — конфликт состояния или дубликат; 422 — неверные данные; 413 — файл больше 5 МБ.
"""


@asynccontextmanager
async def lifespan(app):
    if len(JWT_SECRET) < 32 or JWT_SECRET == "GENERATE_WITH_CONFIGURE_SCRIPT":
        raise RuntimeError("Создайте случайный JWT_SECRET: python scripts/configure.py")
    STORAGE.mkdir(parents=True, exist_ok=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield


def create_api(version):
    api = FastAPI(title="Олимпиадное движение — " + version, version=version,
                  description=DESCRIPTION, docs_url=None, redoc_url=None,
                  responses={code: {"model": ErrorRead, "description": description}
                      for code, description in {
                          400: "Неверный текущий пароль",
                          401: "Требуется вход", 403: "Недостаточно прав",
                          404: "Не найдено", 409: "Конфликт данных или состояния",
                          413: "Файл слишком большой", 422: "Ошибка входных данных"
                      }.items()})
    api.include_router(auth.router)
    api.include_router(users.router)
    if version == "v2":
        api.include_router(olympiads.v2_router)
        # Общая реализация обеспечивает одинаковые права в обеих версиях.
        common_router = APIRouter()
        for route in olympiads.router.routes:
            if route.path != "/olympiads" or "GET" not in route.methods:
                common_router.routes.append(route)
        api.include_router(common_router)
    else:
        api.include_router(olympiads.router)
    for router in (participations.router, protocols.router, attachments.router):
        api.include_router(router)

    @api.get("/docs", include_in_schema=False)
    def swagger():
        return get_swagger_ui_html(openapi_url=f"/api/{version}/openapi.json",
            title=f"Документация {version}", swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css", swagger_favicon_url="data:,")

    @api.get("/redoc", include_in_schema=False)
    def redoc():
        return get_redoc_html(openapi_url=f"/api/{version}/openapi.json",
            title=f"ReDoc {version}", redoc_js_url="/static/redoc.standalone.js",
            redoc_favicon_url="data:,", with_google_fonts=False)
    return api


app = FastAPI(title="REST-сервис олимпиад", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


@app.get("/health", tags=["Состояние"], summary="Проверить подключение к БД")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql"}


app.mount("/api/v1", create_api("v1"))
app.mount("/api/v2", create_api("v2"))

