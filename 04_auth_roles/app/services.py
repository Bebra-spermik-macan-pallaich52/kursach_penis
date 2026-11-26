from app.errors import log_error
from app.database import fetch_one
from fastapi import HTTPException
from app.models.olympiad import Olympiad
from app.models.user import User


async def save(db):
    try:
        await db.commit()
    except Exception as error:
        log_error(error, "save")
        raise


async def get_user(db, user_id):
    try:
        row = await fetch_one(db, "SELECT * FROM users WHERE id = %s", (user_id,))
        if not row:
            raise HTTPException(404, "Пользователь не найден")
        return User(**row)
    except Exception as error:
        log_error(error, "get_user")
        raise


async def get_olympiad(db, olympiad_id, lock=False):
    try:
        query = "SELECT * FROM olympiads WHERE id = %s"
        if lock:
            query += " FOR UPDATE"
        row = await fetch_one(db, query, (olympiad_id,))
        if not row:
            raise HTTPException(404, "Олимпиада не найдена")
        return Olympiad(**row)
    except Exception as error:
        log_error(error, "get_olympiad")
        raise


def check_owner(olympiad, user):
    try:
        if user.role != "admin" and olympiad.teacher_id != user.id:
            raise HTTPException(403, "Это олимпиада другого преподавателя")
    except Exception as error:
        log_error(error, "check_owner")
        raise


def check_draft(olympiad):
    try:
        if olympiad.protocol_status != "draft":
            raise HTTPException(409, "Изменения доступны только при статусе draft")
    except Exception as error:
        log_error(error, "check_draft")
        raise


async def check_teacher(db, teacher_id):
    try:
        row = await fetch_one(db, "SELECT role, is_active FROM users WHERE id = %s", (teacher_id,))
        if not row or row["role"] != "teacher" or (not row["is_active"]):
            raise HTTPException(422, "Ответственным должен быть действующий преподаватель")
    except Exception as error:
        log_error(error, "check_teacher")
        raise
