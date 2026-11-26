from app.errors import log_error
from app.database import fetch_all, fetch_one
from app.validation import Id
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg import AsyncConnection
from app.database import get_db, execute
from app.models.olympiad import Olympiad
from app.models.user import User
from app.schemas.olympiad_create import OlympiadCreate
from app.schemas.olympiad_update import OlympiadUpdate
from app.schemas.olympiad_read import OlympiadRead
from app.schemas.olympiad_page import OlympiadPage
from app.schemas.api_model import has_invalid_text
from app.security import require_admin
from app.records import insert_olympiad, update_fields
from app.services import check_draft, check_teacher, get_olympiad, save

router = APIRouter(tags=["Олимпиады"])
v2_router = APIRouter(tags=["Олимпиады v2"])


def filter_olympiads(year, search=None):
    try:
        conditions = []
        values = []
        if year is not None:
            conditions.append("EXTRACT(YEAR FROM start_date) = %s")
            values.append(year)
        if search:
            if has_invalid_text(search):
                raise HTTPException(422, "Некорректный текст поиска")
            conditions.append("strpos(lower(title), lower(%s)) > 0")
            values.append(search)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        return (where, values)
    except Exception as error:
        log_error(error, "filter_olympiads")
        raise


@router.get(
    "/olympiads", response_model=list[OlympiadRead], summary="Все олимпиады, фильтр по году"
)
async def list_olympiads(
    year: int | None = Query(default=None, ge=2000, le=2100), db: AsyncConnection = Depends(get_db)
):
    try:
        where, values = filter_olympiads(year)
        return await fetch_all(
            db, "SELECT * FROM olympiads" + where + " ORDER BY start_date, id", values
        )
    except Exception as error:
        log_error(error, "list_olympiads")
        raise


@v2_router.get(
    "/olympiads", response_model=OlympiadPage, summary="Олимпиады: поиск, год, пагинация"
)
async def list_olympiads_v2(
    year: int | None = Query(default=None, ge=2000, le=2100),
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, alias="pageSize", ge=1, le=100),
    db: AsyncConnection = Depends(get_db),
):
    try:
        where, values = filter_olympiads(year, search)
        total = (await fetch_one(db, "SELECT count(*) AS total FROM olympiads" + where, values))[
            "total"
        ]
        items = await fetch_all(
            db,
            "SELECT * FROM olympiads" + where + " ORDER BY start_date, id LIMIT %s OFFSET %s",
            [*values, page_size, (page - 1) * page_size],
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except Exception as error:
        log_error(error, "list_olympiads_v2")
        raise


@router.get("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Карточка олимпиады")
async def olympiad_detail(olympiad_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        return await get_olympiad(db, olympiad_id)
    except Exception as error:
        log_error(error, "olympiad_detail")
        raise


@router.post(
    "/olympiads", response_model=OlympiadRead, status_code=201, summary="Создать олимпиаду"
)
async def create_olympiad(
    data: OlympiadCreate, user: User = Depends(require_admin), db: AsyncConnection = Depends(get_db)
):
    try:
        await check_teacher(db, data.teacher_id)
        item = await insert_olympiad(db, Olympiad(**data.model_dump()))
        await save(db)
        return item
    except Exception as error:
        log_error(error, "create_olympiad")
        raise


@router.patch(
    "/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Изменить поля карточки"
)
async def patch_olympiad(
    olympiad_id: Id,
    data: OlympiadUpdate,
    user: User = Depends(require_admin),
    db: AsyncConnection = Depends(get_db),
):
    try:
        item = await get_olympiad(db, olympiad_id, lock=True)
        check_draft(item)
        values = data.model_dump(exclude_unset=True)
        if "teacher_id" in values:
            await check_teacher(db, values["teacher_id"])
        if values.get("end_date", item.end_date) < values.get("start_date", item.start_date):
            raise HTTPException(422, "Окончание не может быть раньше начала")
        await update_fields(db, "olympiads", item.id, values)
        await save(db)
        return await get_olympiad(db, item.id)
    except Exception as error:
        log_error(error, "patch_olympiad")
        raise


@router.put(
    "/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Заменить данные карточки"
)
async def replace_olympiad(
    olympiad_id: Id,
    data: OlympiadCreate,
    user: User = Depends(require_admin),
    db: AsyncConnection = Depends(get_db),
):
    try:
        return await patch_olympiad(olympiad_id, OlympiadUpdate(**data.model_dump()), user, db)
    except Exception as error:
        log_error(error, "replace_olympiad")
        raise


@router.delete("/olympiads/{olympiad_id}", status_code=204, summary="Удалить пустую олимпиаду")
async def delete_olympiad(
    olympiad_id: Id, user: User = Depends(require_admin), db: AsyncConnection = Depends(get_db)
):
    try:
        item = await get_olympiad(db, olympiad_id, lock=True)
        check_draft(item)
        linked = (
            await fetch_one(
                db,
                """
                    SELECT EXISTS(SELECT 1 FROM participations WHERE olympiad_id = %s)
                        OR EXISTS(SELECT 1 FROM attachments WHERE olympiad_id = %s) AS found
                """,
                (item.id, item.id),
            )
        )["found"]
        if linked:
            raise HTTPException(409, "Сначала удалите записи участия и документы")
        await execute(db, "DELETE FROM olympiads WHERE id = %s", (item.id,))
        await save(db)
        return Response(status_code=204)
    except Exception as error:
        log_error(error, "delete_olympiad")
        raise
