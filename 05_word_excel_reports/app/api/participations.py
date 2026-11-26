from app.errors import log_error
from app.database import fetch_all, fetch_one
from app.validation import Id
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Response
from psycopg import AsyncConnection
from app.database import get_db, execute
from app.models.user import User
from app.models.participation import Participation
from app.schemas.result_update import ResultUpdate
from app.schemas.participation_read import ParticipationRead
from app.schemas.my_participation_read import MyParticipationRead
from app.security import get_current_user, require_staff
from app.records import insert_participation, update_fields
from app.services import check_draft, check_owner, get_olympiad, get_user, save

router = APIRouter(tags=["Участие и результаты"])


def participation_data(item, student, show_result=True):
    try:
        return {
            "id": item.id,
            "olympiadId": item.olympiad_id,
            "studentId": item.student_id,
            "fullName": student.full_name,
            "score": float(item.score) if item.score is not None and show_result else None,
            "result": item.result if show_result else None,
        }
    except Exception as error:
        log_error(error, "participation_data")
        raise


async def get_participation(db, participation_id):
    try:
        row = await fetch_one(db, "SELECT * FROM participations WHERE id = %s", (participation_id,))
        if not row:
            raise HTTPException(404, "Заявка не найдена")
        return Participation(**row)
    except Exception as error:
        log_error(error, "get_participation")
        raise


@router.post(
    "/olympiads/{olympiad_id}/participations",
    response_model=ParticipationRead,
    status_code=201,
    summary="Записаться на олимпиаду",
)
async def enroll(
    olympiad_id: Id, user: User = Depends(get_current_user), db: AsyncConnection = Depends(get_db)
):
    try:
        if user.role != "student":
            raise HTTPException(403, "Записываться может только студент")
        olympiad = await get_olympiad(db, olympiad_id, lock=True)
        check_draft(olympiad)
        if olympiad.end_date < date.today():
            raise HTTPException(409, "Приём заявок завершён")
        item = await insert_participation(
            db, Participation(olympiad_id=olympiad.id, student_id=user.id)
        )
        await save(db)
        return participation_data(item, user, False)
    except Exception as error:
        log_error(error, "enroll")
        raise


@router.get(
    "/users/me/participations",
    response_model=list[MyParticipationRead],
    summary="Свои заявки и опубликованные результаты",
)
async def my_participations(
    user: User = Depends(get_current_user), db: AsyncConnection = Depends(get_db)
):
    try:
        rows = await fetch_all(
            db,
            """
                SELECT p.*, o.title, o.protocol_status FROM participations p
                JOIN olympiads o ON o.id = p.olympiad_id WHERE p.student_id = %s ORDER BY p.id
            """,
            (user.id,),
        )
        data = []
        for row in rows:
            title, status = (row.pop("title"), row.pop("protocol_status"))
            item = participation_data(Participation(**row), user, status == "published")
            item.update({"title": title, "protocolStatus": status})
            data.append(item)
        return data
    except Exception as error:
        log_error(error, "my_participations")
        raise


@router.get(
    "/olympiads/{olympiad_id}/participations",
    response_model=list[ParticipationRead],
    summary="Заявки для ответственного преподавателя",
)
async def list_participations(
    olympiad_id: Id, user: User = Depends(require_staff), db: AsyncConnection = Depends(get_db)
):
    try:
        check_owner(await get_olympiad(db, olympiad_id), user)
        return await fetch_all(
            db,
            """
                SELECT p.*, u.full_name FROM participations p JOIN users u ON u.id = p.student_id
                WHERE p.olympiad_id = %s ORDER BY p.id
            """,
            (olympiad_id,),
        )
    except Exception as error:
        log_error(error, "list_participations")
        raise


@router.put(
    "/participations/{participation_id}/result",
    response_model=ParticipationRead,
    summary="Записать баллы и результат",
)
async def update_result(
    participation_id: Id,
    data: ResultUpdate,
    user: User = Depends(require_staff),
    db: AsyncConnection = Depends(get_db),
):
    try:
        item = await get_participation(db, participation_id)
        olympiad = await get_olympiad(db, item.olympiad_id, lock=True)
        check_owner(olympiad, user)
        check_draft(olympiad)
        await update_fields(db, "participations", item.id, data.model_dump())
        await save(db)
        return participation_data(
            await get_participation(db, item.id), await get_user(db, item.student_id)
        )
    except Exception as error:
        log_error(error, "update_result")
        raise


@router.delete(
    "/participations/{participation_id}",
    status_code=204,
    summary="Удалить заявку до подготовки протокола",
)
async def cancel(
    participation_id: Id,
    user: User = Depends(get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    try:
        item = await get_participation(db, participation_id)
        olympiad = await get_olympiad(db, item.olympiad_id, lock=True)
        if user.role == "student":
            if item.student_id != user.id:
                raise HTTPException(403, "Это заявка другого студента")
        else:
            check_owner(olympiad, user)
        check_draft(olympiad)
        await execute(db, "DELETE FROM participations WHERE id = %s", (item.id,))
        await save(db)
        return Response(status_code=204)
    except Exception as error:
        log_error(error, "cancel")
        raise
