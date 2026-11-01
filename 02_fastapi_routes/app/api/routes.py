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


@router.get("/users")
def users(db: Session = Depends(get_db)):
    return [user_data(user) for user in db.query(User).order_by(User.id).all()]


@router.post("/users", status_code=201)
def create_user(data: dict, db: Session = Depends(get_db)):
    values = read_user(data)
    password = values.pop("password")
    user = User(**values, password_hash=hash_password(password))
    db.add(user)
    save(db)
    return user_data(user)


@router.get("/olympiads")
def olympiads(year: int | None = Query(default=None, ge=2000, le=2100), db: Session = Depends(get_db)):
    query = db.query(Olympiad)
    if year is not None:
        query = query.filter(extract("year", Olympiad.start_date) == year)
    return query.order_by(Olympiad.id).all()


@router.get("/olympiads/{olympiad_id}")
def olympiad(olympiad_id: int, db: Session = Depends(get_db)):
    return get_olympiad(db, olympiad_id)


@router.post("/olympiads", status_code=201)
def create_olympiad(data: dict, db: Session = Depends(get_db)):
    values = read_olympiad(data)
    check_teacher(db, values["teacher_id"])
    item = Olympiad(**values)
    db.add(item)
    save(db)
    return item


@router.patch("/olympiads/{olympiad_id}")
def update_olympiad(olympiad_id: int, data: dict, db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    values = read_update(data)
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


@router.post("/olympiads/{olympiad_id}/participants/{student_id}", status_code=201)
def enroll(olympiad_id: int, student_id: int, db: Session = Depends(get_db)):
    get_olympiad(db, olympiad_id)
    student = db.get(User, student_id)
    if not student or student.role != "student" or not student.is_active:
        raise HTTPException(422, "Нужен действующий студент")
    part = Participation(olympiad_id=olympiad_id, student_id=student_id)
    db.add(part)
    save(db)
    return participation_data(part, student)


@router.get("/olympiads/{olympiad_id}/participants")
def participants(olympiad_id: int, db: Session = Depends(get_db)):
    get_olympiad(db, olympiad_id)
    rows = db.query(Participation, User).join(User, User.id == Participation.student_id).filter(
        Participation.olympiad_id == olympiad_id).order_by(Participation.id).all()
    return [participation_data(part, student) for part, student in rows]


def check_text(data):
    for value in data.values():
        if isinstance(value, str) and any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF or ord(char) in (0xFFFE, 0xFFFF) for char in value):
            raise HTTPException(422, "Текст содержит недопустимые символы")


def read_update(data):
    check_text(data)
    fields = {"title", "description", "teacher_id", "start_date", "end_date"}
    if set(data) - fields or any(value is None for value in data.values()):
        raise HTTPException(422, "Неверные поля карточки")
    values = dict(data)
    try:
        for key in ("start_date", "end_date"):
            if key in values:
                values[key] = date.fromisoformat(values[key])
        if "teacher_id" in values and (type(values["teacher_id"]) is not int or values["teacher_id"] <= 0):
            raise ValueError()
        for key, minimum, maximum in [("title", 3, 200), ("description", 0, 5000)]:
            if key in values and (not isinstance(values[key], str) or not minimum <= len(values[key]) <= maximum):
                raise ValueError()
    except (TypeError, ValueError):
        raise HTTPException(422, "Проверьте название, преподавателя и даты")
    return values


def read_olympiad(data):
    if not {"title", "teacher_id", "start_date", "end_date"}.issubset(data):
        raise HTTPException(422, "Заполните название, преподавателя и даты")
    values = read_update(data)
    if values["end_date"] < values["start_date"]:
        raise HTTPException(422, "Неверный порядок дат")
    return values


def read_user(data):
    check_text(data)
    fields = {"username", "password", "full_name", "email", "role", "birth_date", "institution",
              "education_level", "course", "specialty"}
    required = {"username", "password", "full_name", "email", "role"}
    if set(data) - fields or not required.issubset(data):
        raise HTTPException(422, "Проверьте поля пользователя")
    values = dict(data)
    try:
        for key, minimum, maximum in [("username", 3, 50), ("password", 8, 128), ("full_name", 5, 150), ("email", 3, 254)]:
            if not isinstance(values[key], str) or not minimum <= len(values[key]) <= maximum:
                raise ValueError()
        if not values["username"].isascii() or not values["username"].replace("_", "").isalnum():
            raise ValueError()
        if "@" not in values["email"] or values["role"] not in ("teacher", "student"):
            raise ValueError()
        if "birth_date" in values:
            values["birth_date"] = date.fromisoformat(values["birth_date"])
            if values["birth_date"] >= date.today():
                raise ValueError()
        for key, maximum in [("institution", 200), ("education_level", 100), ("specialty", 150)]:
            if key in values and (not isinstance(values[key], str) or len(values[key]) > maximum):
                raise ValueError()
        if "course" in values and (type(values["course"]) is not int or not 1 <= values["course"] <= 6):
            raise ValueError()
        if values["role"] == "student" and not all(values.get(key) for key in ("birth_date", "institution", "education_level", "course", "specialty")):
            raise ValueError()
        if any(isinstance(value, str) and any(ord(char) < 32 for char in value) for value in values.values()):
            raise ValueError()
    except (TypeError, ValueError):
        raise HTTPException(422, "Проверьте данные пользователя")
    return values
