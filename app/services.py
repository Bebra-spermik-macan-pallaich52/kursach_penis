"""Общие проверки, используемые в нескольких маршрутах."""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.models.olympiad import Olympiad
from app.models.user import User


def save(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Такая запись уже существует или нарушает связи данных")


def get_olympiad(db, olympiad_id, lock=False):
    query = db.query(Olympiad).filter(Olympiad.id == olympiad_id)
    if lock:
        query = query.with_for_update()
    item = query.first()
    if not item:
        raise HTTPException(404, "Олимпиада не найдена")
    return item


def check_owner(olympiad, user):
    if user.role != "admin" and olympiad.teacher_id != user.id:
        raise HTTPException(403, "Это олимпиада другого преподавателя")


def check_draft(olympiad):
    if olympiad.protocol_status != "draft":
        raise HTTPException(409, "Изменения доступны только при статусе draft")


def check_teacher(db, teacher_id):
    teacher = db.get(User, teacher_id)
    if not teacher or teacher.role != "teacher" or not teacher.is_active:
        raise HTTPException(422, "Ответственным должен быть действующий преподаватель")

