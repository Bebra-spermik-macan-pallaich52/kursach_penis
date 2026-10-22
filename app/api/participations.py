from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.schemas.result_update import ResultUpdate
from app.schemas.participation_read import ParticipationRead
from app.schemas.my_participation_read import MyParticipationRead
from app.security import get_current_user, require_staff
from app.services import check_draft, check_owner, get_olympiad, save

router = APIRouter(tags=["Участие и результаты"])


def participation_data(item, student, show_result=True):
    return {"id": item.id, "olympiadId": item.olympiad_id,
            "studentId": item.student_id, "fullName": student.full_name,
            "score": float(item.score) if item.score is not None and show_result else None,
            "result": item.result if show_result else None}


@router.post("/olympiads/{olympiad_id}/participations", response_model=ParticipationRead, status_code=201, summary="Записаться на олимпиаду")
def enroll(olympiad_id: int, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(403, "Записываться может только студент")
    olympiad = get_olympiad(db, olympiad_id, lock=True)
    check_draft(olympiad)
    if olympiad.end_date < date.today():
        raise HTTPException(409, "Приём заявок завершён")
    item = Participation(olympiad_id=olympiad.id, student_id=user.id)
    db.add(item)
    save(db)
    return participation_data(item, user, False)


@router.get("/users/me/participations", response_model=list[MyParticipationRead], summary="Свои заявки и опубликованные результаты")
def my_participations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Participation, Olympiad).join(Olympiad).filter(Participation.student_id == user.id).order_by(Participation.id).all()
    data = []
    for item, olympiad in rows:
        row = participation_data(item, user, olympiad.protocol_status == "published")
        row.update({"title": olympiad.title, "protocolStatus": olympiad.protocol_status})
        data.append(row)
    return data


@router.get("/olympiads/{olympiad_id}/participations", response_model=list[ParticipationRead], summary="Заявки для ответственного преподавателя")
def list_participations(olympiad_id: int, user: User = Depends(require_staff),
                        db: Session = Depends(get_db)):
    olympiad = get_olympiad(db, olympiad_id)
    check_owner(olympiad, user)
    rows = db.query(Participation, User).join(User, User.id == Participation.student_id).filter(Participation.olympiad_id == olympiad_id).order_by(Participation.id).all()
    return [participation_data(item, student) for item, student in rows]


@router.put("/participations/{participation_id}/result", response_model=ParticipationRead, summary="Записать баллы и результат")
def update_result(participation_id: int, data: ResultUpdate,
                   user: User = Depends(require_staff), db: Session = Depends(get_db)):
    item = db.get(Participation, participation_id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    olympiad = get_olympiad(db, item.olympiad_id, lock=True)
    check_owner(olympiad, user)
    check_draft(olympiad)
    item.score = data.score
    item.result = data.result
    save(db)
    return participation_data(item, db.get(User, item.student_id))


@router.delete("/participations/{participation_id}", status_code=204, summary="Удалить заявку до подготовки протокола")
def cancel(participation_id: int, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    item = db.get(Participation, participation_id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    olympiad = get_olympiad(db, item.olympiad_id, lock=True)
    if user.role == "student":
        if item.student_id != user.id:
            raise HTTPException(403, "Это заявка другого студента")
    else:
        check_owner(olympiad, user)
    check_draft(olympiad)
    db.delete(item)
    save(db)
    return Response(status_code=204)

