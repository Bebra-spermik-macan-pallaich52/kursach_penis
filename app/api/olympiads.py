from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import extract
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.olympiad_create import OlympiadCreate
from app.schemas.olympiad_update import OlympiadUpdate
from app.schemas.olympiad_read import OlympiadRead
from app.schemas.olympiad_page import OlympiadPage
from app.security import require_admin
from app.services import check_draft, check_teacher, get_olympiad, save

router = APIRouter(tags=["Олимпиады"])
v2_router = APIRouter(tags=["Олимпиады v2"])


def filtered_query(db, year=None, search=None):
    query = db.query(Olympiad)
    if year:
        query = query.filter(extract("year", Olympiad.start_date) == year)
    if search:
        # autoescape не даёт символам % и _ превратиться в шаблон поиска.
        query = query.filter(Olympiad.title.icontains(search, autoescape=True))
    return query.order_by(Olympiad.start_date, Olympiad.id)


@router.get("/olympiads", response_model=list[OlympiadRead], summary="Все олимпиады, фильтр по году")
def list_olympiads(year: int | None = Query(default=None, ge=2000, le=2100),
                   db: Session = Depends(get_db)):
    return filtered_query(db, year).all()


@v2_router.get("/olympiads", response_model=OlympiadPage, summary="Олимпиады: поиск, год, пагинация")
def list_olympiads_v2(year: int | None = Query(default=None, ge=2000, le=2100),
                      search: str | None = Query(default=None, max_length=100),
                      page: int = Query(default=1, ge=1),
                      page_size: int = Query(default=10, alias="pageSize", ge=1, le=100),
                      db: Session = Depends(get_db)):
    query = filtered_query(db, year, search)
    return {"items": query.offset((page - 1) * page_size).limit(page_size).all(),
            "total": query.count(), "page": page, "page_size": page_size}


@router.get("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Карточка олимпиады")
def olympiad_detail(olympiad_id: int, db: Session = Depends(get_db)):
    return get_olympiad(db, olympiad_id)


@router.post("/olympiads", response_model=OlympiadRead, status_code=201, summary="Создать олимпиаду")
def create_olympiad(data: OlympiadCreate, user: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    check_teacher(db, data.teacher_id)
    item = Olympiad(**data.model_dump())
    db.add(item)
    save(db)
    return item


@router.patch("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Изменить поля карточки")
def patch_olympiad(olympiad_id: int, data: OlympiadUpdate,
                   user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_draft(item)
    values = data.model_dump(exclude_unset=True)
    if "teacher_id" in values:
        check_teacher(db, values["teacher_id"])
    start = values.get("start_date", item.start_date)
    end = values.get("end_date", item.end_date)
    if end < start:
        raise HTTPException(422, "Окончание не может быть раньше начала")
    for name, value in values.items():
        setattr(item, name, value)
    save(db)
    return item


@router.put("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Заменить данные карточки")
def replace_olympiad(olympiad_id: int, data: OlympiadCreate,
                     user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return patch_olympiad(olympiad_id, OlympiadUpdate(**data.model_dump()), user, db)


@router.delete("/olympiads/{olympiad_id}", status_code=204, summary="Удалить пустую олимпиаду")
def delete_olympiad(olympiad_id: int, user: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_draft(item)
    if db.query(Participation).filter_by(olympiad_id=item.id).first() or db.query(Attachment).filter_by(olympiad_id=item.id).first():
        raise HTTPException(409, "Сначала удалите записи участия и документы")
    db.delete(item)
    save(db)
    return Response(status_code=204)

