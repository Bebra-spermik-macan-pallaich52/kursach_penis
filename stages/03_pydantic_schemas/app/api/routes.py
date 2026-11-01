from app.schemas.user_create import UserCreate
from app.schemas.user_read import UserRead
from app.schemas.olympiad_create import OlympiadCreate
from app.schemas.olympiad_update import OlympiadUpdate
from app.schemas.olympiad_read import OlympiadRead
from app.schemas.participation_read import ParticipationRead
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.security import hash_password
from app.services import save, get_olympiad, check_teacher

router = APIRouter()


def user_data(user):
    return {name: getattr(user, name) for name in ("id", "username", "full_name", "email", "role",
            "birth_date", "institution", "education_level", "course", "specialty", "is_active")}


def participation_data(part, student):
    return {"id": part.id, "olympiad_id": part.olympiad_id, "student_id": part.student_id,
            "full_name": student.full_name, "score": part.score, "result": part.result}


@router.get("/users", response_model=list[UserRead])
def users(db: Session = Depends(get_db)):
    return [user_data(user) for user in db.query(User).order_by(User.id).all()]


@router.post("/users", status_code=201, response_model=UserRead)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    values = data.model_dump()
    password = values.pop("password")
    user = User(**values, password_hash=hash_password(password))
    db.add(user)
    save(db)
    return user_data(user)


@router.get("/olympiads", response_model=list[OlympiadRead])
def olympiads(year: int | None = Query(default=None, ge=2000, le=2100), db: Session = Depends(get_db)):
    query = db.query(Olympiad)
    if year is not None:
        query = query.filter(extract("year", Olympiad.start_date) == year)
    return query.order_by(Olympiad.id).all()


@router.get("/olympiads/{olympiad_id}", response_model=OlympiadRead)
def olympiad(olympiad_id: int, db: Session = Depends(get_db)):
    return get_olympiad(db, olympiad_id)


@router.post("/olympiads", status_code=201, response_model=OlympiadRead)
def create_olympiad(data: OlympiadCreate, db: Session = Depends(get_db)):
    values = data.model_dump()
    check_teacher(db, values["teacher_id"])
    item = Olympiad(**values)
    db.add(item)
    save(db)
    return item


@router.patch("/olympiads/{olympiad_id}", response_model=OlympiadRead)
def update_olympiad(olympiad_id: int, data: OlympiadUpdate, db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    values = data.model_dump(exclude_unset=True)
    if "teacher_id" in values:
        check_teacher(db, values["teacher_id"])
    if values.get("end_date", item.end_date) < values.get("start_date", item.start_date):
        raise HTTPException(422, "Неверный порядок дат")
    for name, value in values.items():
        setattr(item, name, value)
    save(db)
    return item


@router.delete("/olympiads/{olympiad_id}", status_code=204)
def delete_olympiad(olympiad_id: int, db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    db.delete(item)
    save(db)


@router.post("/olympiads/{olympiad_id}/participants/{student_id}", status_code=201, response_model=ParticipationRead)
def enroll(olympiad_id: int, student_id: int, db: Session = Depends(get_db)):
    get_olympiad(db, olympiad_id)
    student = db.get(User, student_id)
    if not student or student.role != "student" or not student.is_active:
        raise HTTPException(422, "Нужен действующий студент")
    part = Participation(olympiad_id=olympiad_id, student_id=student_id)
    db.add(part)
    save(db)
    return participation_data(part, student)


@router.get("/olympiads/{olympiad_id}/participants", response_model=list[ParticipationRead])
def participants(olympiad_id: int, db: Session = Depends(get_db)):
    get_olympiad(db, olympiad_id)
    rows = db.query(Participation, User).join(User, User.id == Participation.student_id).filter(
        Participation.olympiad_id == olympiad_id).order_by(Participation.id).all()
    return [participation_data(part, student) for part, student in rows]
