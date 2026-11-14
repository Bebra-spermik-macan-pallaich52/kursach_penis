from fastapi import HTTPException
from app.models.olympiad import Olympiad
from app.models.user import User


def save(db):
    db.commit()


def get_user(db, user_id):
    row = db.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Пользователь не найден")
    return User(**row)


def get_olympiad(db, olympiad_id, lock=False):
    query = "SELECT * FROM olympiads WHERE id = %s"
    if lock:
        query += " FOR UPDATE"
    row = db.execute(query, (olympiad_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Олимпиада не найдена")
    return Olympiad(**row)


def check_owner(olympiad, user):
    if user.role != "admin" and olympiad.teacher_id != user.id:
        raise HTTPException(403, "Это олимпиада другого преподавателя")


def check_draft(olympiad):
    if olympiad.protocol_status != "draft":
        raise HTTPException(409, "Изменения доступны только при статусе draft")


def check_teacher(db, teacher_id):
    row = db.execute("SELECT role, is_active FROM users WHERE id = %s", (teacher_id,)).fetchone()
    if not row or row["role"] != "teacher" or not row["is_active"]:
        raise HTTPException(422, "Ответственным должен быть действующий преподаватель")
