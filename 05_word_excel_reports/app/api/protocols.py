from app.errors import log_error
from app.database import fetch_all, fetch_one
import asyncio
from app.validation import Id
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from psycopg import AsyncConnection
from app.database import get_db, execute
from app.models.user import User
from app.schemas.protocol_update import ProtocolUpdate
from app.schemas.olympiad_read import OlympiadRead
from app.schemas.protocol_read import ProtocolRead
from app.schemas.status_read import StatusRead
from app.security import require_admin, require_staff
from app.services import check_owner, get_olympiad, save
from app.reports import RESULT_NAMES, make_report

router = APIRouter(tags=["Протоколы и отчёты"])
REPORT_RESPONSE = {
    200: {
        "description": "Документ Word или Excel",
        "content": {
            media: {"schema": {"type": "string", "format": "binary"}}
            for media in (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    }
}


async def protocol_rows(db, olympiad_id):
    try:
        rows = await fetch_all(
            db,
            """
                SELECT p.*, u.full_name FROM participations p JOIN users u ON u.id = p.student_id
                WHERE p.olympiad_id = %s ORDER BY p.score DESC NULLS LAST, p.id
            """,
            (olympiad_id,),
        )
        return rows
    except Exception as error:
        log_error(error, "protocol_rows")
        raise


async def protocol_data(db, item):
    try:
        return {
            "olympiadId": item.id,
            "title": item.title,
            "status": item.protocol_status,
            "participants": await protocol_rows(db, item.id),
        }
    except Exception as error:
        log_error(error, "protocol_data")
        raise


@router.get(
    "/protocols",
    response_model=list[OlympiadRead],
    summary="Состояния протоколов (служебный список)",
)
async def list_protocols(
    user: User = Depends(require_staff), db: AsyncConnection = Depends(get_db)
):
    try:
        if user.role == "teacher":
            return await fetch_all(
                db, "SELECT * FROM olympiads WHERE teacher_id = %s ORDER BY id", (user.id,)
            )
        return await fetch_all(db, "SELECT * FROM olympiads ORDER BY id")
    except Exception as error:
        log_error(error, "list_protocols")
        raise


@router.get(
    "/olympiads/{olympiad_id}/protocol",
    response_model=ProtocolRead,
    summary="Опубликованный протокол (общедоступный)",
)
async def public_protocol(olympiad_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        item = await get_olympiad(db, olympiad_id)
        if item.protocol_status != "published":
            raise HTTPException(404, "Протокол ещё не опубликован")
        return await protocol_data(db, item)
    except Exception as error:
        log_error(error, "public_protocol")
        raise


@router.get(
    "/olympiads/{olympiad_id}/protocol-draft",
    response_model=ProtocolRead,
    summary="Просмотреть служебный протокол",
)
async def private_protocol(
    olympiad_id: Id, user: User = Depends(require_staff), db: AsyncConnection = Depends(get_db)
):
    try:
        item = await get_olympiad(db, olympiad_id)
        check_owner(item, user)
        return await protocol_data(db, item)
    except Exception as error:
        log_error(error, "private_protocol")
        raise


@router.patch(
    "/olympiads/{olympiad_id}/protocol",
    response_model=StatusRead,
    summary="Подготовить, отозвать или опубликовать протокол",
)
async def set_protocol_status(
    olympiad_id: Id,
    data: ProtocolUpdate,
    user: User = Depends(require_staff),
    db: AsyncConnection = Depends(get_db),
):
    try:
        item = await get_olympiad(db, olympiad_id, lock=True)
        check_owner(item, user)
        current = item.protocol_status
        if data.status == "published" and user.role != "admin":
            raise HTTPException(403, "Публикует только администратор")
        if (current, data.status) not in [
            ("draft", "prepared"),
            ("prepared", "draft"),
            ("prepared", "published"),
        ]:
            raise HTTPException(409, "Недопустимый переход статуса протокола")
        if data.status == "prepared":
            if item.end_date > date.today():
                raise HTTPException(409, "Олимпиада ещё не завершена")
            counts = await fetch_one(
                db,
                """
                    SELECT count(*) AS total, count(*) FILTER (WHERE score IS NULL OR result IS NULL) AS missing
                    FROM participations WHERE olympiad_id = %s
                """,
                (item.id,),
            )
            if not counts["total"] or counts["missing"]:
                raise HTTPException(409, "Укажите баллы и результат каждого участника")
        await execute(
            db, "UPDATE olympiads SET protocol_status = %s WHERE id = %s", (data.status, item.id)
        )
        await save(db)
        item.protocol_status = data.status
        return {"status": item.protocol_status}
    except Exception as error:
        log_error(error, "set_protocol_status")
        raise


@router.get(
    "/olympiads/{olympiad_id}/reports/protocol",
    response_class=Response,
    responses=REPORT_RESPONSE,
    summary="Скачать протокол Word или Excel",
)
async def export_protocol(
    olympiad_id: Id,
    file_format: str = Query(default="docx", alias="format"),
    user: User = Depends(require_staff),
    db: AsyncConnection = Depends(get_db),
):
    try:
        item = await get_olympiad(db, olympiad_id)
        check_owner(item, user)
        rows = []
        for number, row in enumerate(await protocol_rows(db, item.id), 1):
            rows.append(
                [
                    number,
                    row["full_name"],
                    float(row["score"]) if row["score"] is not None else "—",
                    RESULT_NAMES.get(row["result"], "Не определён"),
                ]
            )
        title = f"Протокол: {item.title}. Статус: {item.protocol_status}"
        return await asyncio.to_thread(
            make_report,
            title,
            ["№", "ФИО", "Баллы", "Результат"],
            rows,
            file_format,
            f"protocol_{item.id}",
        )
    except Exception as error:
        log_error(error, "export_protocol")
        raise


@router.get(
    "/reports/annual",
    response_class=Response,
    responses=REPORT_RESPONSE,
    summary="Годовой отчёт по опубликованным результатам",
)
async def annual_report(
    year: int = Query(ge=2000, le=2100),
    file_format: str = Query(default="xlsx", alias="format"),
    user: User = Depends(require_admin),
    db: AsyncConnection = Depends(get_db),
):
    try:
        rows = await fetch_all(
            db,
            """
                SELECT o.title, o.start_date, u.full_name, p.score, p.result
                FROM olympiads o JOIN participations p ON p.olympiad_id = o.id
                JOIN users u ON u.id = p.student_id
                WHERE EXTRACT(YEAR FROM o.start_date) = %s AND o.protocol_status = 'published'
                ORDER BY o.start_date, o.id, p.id
            """,
            (year,),
        )
        data = [
            [
                row["title"],
                row["start_date"].isoformat(),
                row["full_name"],
                float(row["score"]),
                RESULT_NAMES[row["result"]],
            ]
            for row in rows
        ]
        return await asyncio.to_thread(
            make_report,
            f"Участие студентов в олимпиадах за {year} год. Записей участия: {len(data)}",
            ["Олимпиада", "Дата", "ФИО", "Баллы", "Результат"],
            data,
            file_format,
            f"annual_{year}",
        )
    except Exception as error:
        log_error(error, "annual_report")
        raise
