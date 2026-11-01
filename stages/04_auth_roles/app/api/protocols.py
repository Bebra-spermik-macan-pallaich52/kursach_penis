from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.schemas.protocol_update import ProtocolUpdate
from app.schemas.olympiad_read import OlympiadRead
from app.schemas.protocol_read import ProtocolRead
from app.schemas.status_read import StatusRead
from app.security import require_admin, require_staff
from app.services import check_owner, get_olympiad, save
from app.api.participations import participation_data

router = APIRouter(tags=["Протоколы и отчёты"])


def protocol_rows(db, olympiad_id):
    return db.query(Participation, User).join(User, User.id == Participation.student_id).filter(Participation.olympiad_id == olympiad_id).order_by(Participation.score.desc().nullslast(), Participation.id).all()


def protocol_data(db, item):
    return {"olympiadId": item.id, "title": item.title, "status": item.protocol_status,
            "participants": [participation_data(p, s) for p, s in protocol_rows(db, item.id)]}


@router.get("/protocols", response_model=list[OlympiadRead], summary="Состояния протоколов (служебный список)")
def list_protocols(user: User = Depends(require_staff), db: Session = Depends(get_db)):
    query = db.query(Olympiad)
    if user.role == "teacher":
        query = query.filter(Olympiad.teacher_id == user.id)
    return query.order_by(Olympiad.id).all()


@router.get("/olympiads/{olympiad_id}/protocol", response_model=ProtocolRead, summary="Опубликованный протокол (общедоступный)")
def public_protocol(olympiad_id: int, db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    if item.protocol_status != "published":
        raise HTTPException(404, "Протокол ещё не опубликован")
    return protocol_data(db, item)


@router.get("/olympiads/{olympiad_id}/protocol-draft", response_model=ProtocolRead, summary="Просмотреть служебный протокол")
def private_protocol(olympiad_id: int, user: User = Depends(require_staff),
                      db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    check_owner(item, user)
    return protocol_data(db, item)


@router.patch("/olympiads/{olympiad_id}/protocol", response_model=StatusRead, summary="Подготовить, отозвать или опубликовать протокол")
def set_protocol_status(olympiad_id: int, data: ProtocolUpdate,
                         user: User = Depends(require_staff), db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_owner(item, user)
    current = item.protocol_status
    if data.status == "published" and user.role != "admin":
        raise HTTPException(403, "Публикует только администратор")
    if (current, data.status) not in [("draft", "prepared"), ("prepared", "draft"), ("prepared", "published")]:
        raise HTTPException(409, "Недопустимый переход статуса протокола")
    if data.status == "prepared":
        if item.end_date > date.today():
            raise HTTPException(409, "Олимпиада ещё не завершена")
        query = db.query(Participation).filter_by(olympiad_id=item.id)
        if not query.count() or query.filter(or_(Participation.score.is_(None), Participation.result.is_(None))).count():
            raise HTTPException(409, "Укажите баллы и результат каждого участника")
    item.protocol_status = data.status
    save(db)
    return {"status": item.protocol_status}
