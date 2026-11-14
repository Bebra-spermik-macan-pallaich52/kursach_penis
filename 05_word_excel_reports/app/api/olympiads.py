from app.validation import Id
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg import Connection
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
    return where, values


@router.get("/olympiads", response_model=list[OlympiadRead], summary="Все олимпиады, фильтр по году")
def list_olympiads(year: int | None = Query(default=None, ge=2000, le=2100), db: Connection = Depends(get_db)):
    where, values = filter_olympiads(year)
    return db.execute("SELECT * FROM olympiads" + where + " ORDER BY start_date, id", values).fetchall()


@v2_router.get("/olympiads", response_model=OlympiadPage, summary="Олимпиады: поиск, год, пагинация")
def list_olympiads_v2(year: int | None = Query(default=None, ge=2000, le=2100),
                      search: str | None = Query(default=None, max_length=100),
                      page: int = Query(default=1, ge=1),
                      page_size: int = Query(default=10, alias="pageSize", ge=1, le=100),
                      db: Connection = Depends(get_db)):
    where, values = filter_olympiads(year, search)
    total = db.execute("SELECT count(*) AS total FROM olympiads" + where, values).fetchone()["total"]
    items = db.execute("SELECT * FROM olympiads" + where + " ORDER BY start_date, id LIMIT %s OFFSET %s",
                       [*values, page_size, (page - 1) * page_size]).fetchall()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Карточка олимпиады")
def olympiad_detail(olympiad_id: Id, db: Connection = Depends(get_db)):
    return get_olympiad(db, olympiad_id)


@router.post("/olympiads", response_model=OlympiadRead, status_code=201, summary="Создать олимпиаду")
def create_olympiad(data: OlympiadCreate, user: User = Depends(require_admin), db: Connection = Depends(get_db)):
    check_teacher(db, data.teacher_id)
    item = insert_olympiad(db, Olympiad(**data.model_dump()))
    save(db)
    return item


@router.patch("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Изменить поля карточки")
def patch_olympiad(olympiad_id: Id, data: OlympiadUpdate, user: User = Depends(require_admin),
                   db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_draft(item)
    values = data.model_dump(exclude_unset=True)
    if "teacher_id" in values:
        check_teacher(db, values["teacher_id"])
    if values.get("end_date", item.end_date) < values.get("start_date", item.start_date):
        raise HTTPException(422, "Окончание не может быть раньше начала")
    update_fields(db, "olympiads", item.id, values)
    save(db)
    return get_olympiad(db, item.id)


@router.put("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Заменить данные карточки")
def replace_olympiad(olympiad_id: Id, data: OlympiadCreate, user: User = Depends(require_admin),
                     db: Connection = Depends(get_db)):
    return patch_olympiad(olympiad_id, OlympiadUpdate(**data.model_dump()), user, db)


@router.delete("/olympiads/{olympiad_id}", status_code=204, summary="Удалить пустую олимпиаду")
def delete_olympiad(olympiad_id: Id, user: User = Depends(require_admin), db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_draft(item)
    linked = db.execute("""
        SELECT EXISTS(SELECT 1 FROM participations WHERE olympiad_id = %s)
            OR EXISTS(SELECT 1 FROM attachments WHERE olympiad_id = %s) AS found
        """, (item.id, item.id)).fetchone()["found"]
    if linked:
        raise HTTPException(409, "Сначала удалите записи участия и документы")
    execute(db, "DELETE FROM olympiads WHERE id = %s", (item.id,))
    save(db)
    return Response(status_code=204)
