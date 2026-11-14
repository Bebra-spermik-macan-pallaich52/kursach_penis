import re
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


@router.get("/users")
def users(db: Connection = Depends(get_db)):
    return [user_data(User(**row)) for row in db.execute("SELECT * FROM users ORDER BY id")]


@router.post("/users", status_code=201)
def create_user(data: dict, db: Connection = Depends(get_db)):
    values = read_user(data)
    password = values.pop("password")
    user = User(**values, password_hash=hash_password(password))
    insert_user(db, user)
    save(db)
    return user_data(user)


@router.get("/olympiads")
def olympiads(year: int | None = Query(default=None, ge=2000, le=2100), db: Connection = Depends(get_db)):
    if year is not None:
        return db.execute("SELECT * FROM olympiads WHERE EXTRACT(YEAR FROM start_date) = %s ORDER BY id", (year,)).fetchall()
    return db.execute("SELECT * FROM olympiads ORDER BY id").fetchall()


@router.get("/olympiads/{olympiad_id}")
def olympiad(olympiad_id: Id, db: Connection = Depends(get_db)):
    return get_olympiad(db, olympiad_id)


@router.post("/olympiads", status_code=201)
def create_olympiad(data: dict, db: Connection = Depends(get_db)):
    values = read_olympiad(data)
    check_teacher(db, values["teacher_id"])
    item = Olympiad(**values)
    insert_olympiad(db, item)
    save(db)
    return item


@router.patch("/olympiads/{olympiad_id}")
def update_olympiad(olympiad_id: Id, data: dict, db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    values = read_update(data)
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


@router.post("/olympiads/{olympiad_id}/participants/{student_id}", status_code=201)
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


@router.get("/olympiads/{olympiad_id}/participants")
def participants(olympiad_id: Id, db: Connection = Depends(get_db)):
    get_olympiad(db, olympiad_id)
    return db.execute("""
        SELECT p.*, u.full_name FROM participations p JOIN users u ON u.id = p.student_id
        WHERE p.olympiad_id = %s ORDER BY p.id
        """, (olympiad_id,)).fetchall()



def check_text(data):
    for value in data.values():
        if isinstance(value, str) and any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF or ord(char) in (0xFFFE, 0xFFFF) for char in value):
            raise HTTPException(422, "Текст содержит недопустимые символы")


def read_update(data):
    check_text(data)
    fields = {"title", "description", "teacher_id", "start_date", "end_date"}
    if set(data) - fields or any(value is None for value in data.values()):
        raise HTTPException(422, "Неверные поля карточки")
    values = {name: value.strip() if isinstance(value, str) and name != "password" else value for name, value in data.items()}
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
    if not 2000 <= values["start_date"].year <= 2100 or not 2000 <= values["end_date"].year <= 2100:
        raise HTTPException(422, "Год должен быть от 2000 до 2100")
    return values


def read_user(data):
    check_text(data)
    fields = {"username", "password", "full_name", "email", "role", "birth_date", "institution",
              "education_level", "course", "specialty"}
    required = {"username", "password", "full_name", "email", "role"}
    if set(data) - fields or not required.issubset(data):
        raise HTTPException(422, "Проверьте поля пользователя")
    values = {name: value.strip() if isinstance(value, str) and name != "password" else value for name, value in data.items()}
    try:
        for key, minimum, maximum in [("username", 3, 50), ("password", 8, 128), ("full_name", 5, 150), ("email", 3, 254)]:
            if not isinstance(values[key], str) or not minimum <= len(values[key]) <= maximum:
                raise ValueError()
        if not values["username"].isascii() or not values["username"].replace("_", "").isalnum():
            raise ValueError()
        if not values["password"].strip():
            raise ValueError()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values["email"]) or values["role"] not in ("teacher", "student"):
            raise ValueError()
        if "birth_date" in values:
            values["birth_date"] = date.fromisoformat(values["birth_date"])
            if not date(1900, 1, 1) <= values["birth_date"] < date.today():
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
