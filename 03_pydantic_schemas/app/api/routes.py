from app.schemas.user_create import UserCreate
from app.schemas.user_read import UserRead
from app.schemas.olympiad_create import OlympiadCreate
from app.schemas.olympiad_update import OlympiadUpdate
from app.schemas.olympiad_read import OlympiadRead
from app.schemas.participation_read import ParticipationRead
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection
from app.database import get_db, execute
from app.models.user import User
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.security import hash_password
from app.services import save, get_olympiad, check_teacher
from app.records import insert_user, insert_olympiad, insert_participation, update_fields
from app.validation import Id

router = APIRouter()


def user_data(user):
    return {name: getattr(user, name) for name in ("id", "username", "full_name", "email", "role",
            "birth_date", "institution", "education_level", "course", "specialty", "is_active")}


def participation_data(part, student):
    return {"id": part.id, "olympiad_id": part.olympiad_id, "student_id": part.student_id,
            "full_name": student.full_name, "score": part.score, "result": part.result}


@router.get("/users", response_model=list[UserRead])
def users(db: Connection = Depends(get_db)):
    return [user_data(User(**row)) for row in db.execute("SELECT * FROM users ORDER BY id")]


@router.post("/users", status_code=201, response_model=UserRead)
def create_user(data: UserCreate, db: Connection = Depends(get_db)):
    values = data.model_dump()
    password = values.pop("password")
    user = User(**values, password_hash=hash_password(password))
    insert_user(db, user)
    save(db)
    return user_data(user)


@router.get("/olympiads", response_model=list[OlympiadRead])
def olympiads(year: int | None = Query(default=None, ge=2000, le=2100), db: Connection = Depends(get_db)):
    if year is not None:
        return db.execute("SELECT * FROM olympiads WHERE EXTRACT(YEAR FROM start_date) = %s ORDER BY id", (year,)).fetchall()
    return db.execute("SELECT * FROM olympiads ORDER BY id").fetchall()


@router.get("/olympiads/{olympiad_id}", response_model=OlympiadRead)
def olympiad(olympiad_id: Id, db: Connection = Depends(get_db)):
    return get_olympiad(db, olympiad_id)


@router.post("/olympiads", status_code=201, response_model=OlympiadRead)
def create_olympiad(data: OlympiadCreate, db: Connection = Depends(get_db)):
    values = data.model_dump()
    check_teacher(db, values["teacher_id"])
    item = Olympiad(**values)
    insert_olympiad(db, item)
    save(db)
    return item


@router.patch("/olympiads/{olympiad_id}", response_model=OlympiadRead)
def update_olympiad(olympiad_id: Id, data: OlympiadUpdate, db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    values = data.model_dump(exclude_unset=True)
    if "teacher_id" in values:
        check_teacher(db, values["teacher_id"])
    if values.get("end_date", item.end_date) < values.get("start_date", item.start_date):
        raise HTTPException(422, "Неверный порядок дат")
    for name, value in values.items():
        setattr(item, name, value)
    update_fields(db, "olympiads", item.id, values)
    save(db)
    return item


@router.delete("/olympiads/{olympiad_id}", status_code=204)
def delete_olympiad(olympiad_id: Id, db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    execute(db, "DELETE FROM olympiads WHERE id = %s", (item.id,))
    save(db)


@router.post("/olympiads/{olympiad_id}/participants/{student_id}", status_code=201, response_model=ParticipationRead)
def enroll(olympiad_id: Id, student_id: Id, db: Connection = Depends(get_db)):
    get_olympiad(db, olympiad_id)
    row = db.execute("SELECT * FROM users WHERE id = %s", (student_id,)).fetchone()
    student = User(**row) if row else None
    if not student or student.role != "student" or not student.is_active:
        raise HTTPException(422, "Нужен действующий студент")
    part = Participation(olympiad_id=olympiad_id, student_id=student_id)
    insert_participation(db, part)
    save(db)
    return participation_data(part, student)


@router.get("/olympiads/{olympiad_id}/participants", response_model=list[ParticipationRead])
def participants(olympiad_id: Id, db: Connection = Depends(get_db)):
    get_olympiad(db, olympiad_id)
    return db.execute("""
        SELECT p.*, u.full_name FROM participations p JOIN users u ON u.id = p.student_id
        WHERE p.olympiad_id = %s ORDER BY p.id
        """, (olympiad_id,)).fetchall()
