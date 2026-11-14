from app.validation import Id
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from psycopg import Connection
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
REPORT_RESPONSE = {200: {"description": "Документ Word или Excel",
    "content": {media: {"schema": {"type": "string", "format": "binary"}}
        for media in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}}}


def protocol_rows(db, olympiad_id):
    rows = db.execute("""
        SELECT p.*, u.full_name FROM participations p JOIN users u ON u.id = p.student_id
        WHERE p.olympiad_id = %s ORDER BY p.score DESC NULLS LAST, p.id
        """, (olympiad_id,)).fetchall()
    return rows


def protocol_data(db, item):
    return {"olympiadId": item.id, "title": item.title, "status": item.protocol_status,
            "participants": protocol_rows(db, item.id)}


@router.get("/protocols", response_model=list[OlympiadRead], summary="Состояния протоколов (служебный список)")
def list_protocols(user: User = Depends(require_staff), db: Connection = Depends(get_db)):
    if user.role == "teacher":
        return db.execute("SELECT * FROM olympiads WHERE teacher_id = %s ORDER BY id", (user.id,)).fetchall()
    return db.execute("SELECT * FROM olympiads ORDER BY id").fetchall()


@router.get("/olympiads/{olympiad_id}/protocol", response_model=ProtocolRead, summary="Опубликованный протокол (общедоступный)")
def public_protocol(olympiad_id: Id, db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    if item.protocol_status != "published":
        raise HTTPException(404, "Протокол ещё не опубликован")
    return protocol_data(db, item)


@router.get("/olympiads/{olympiad_id}/protocol-draft", response_model=ProtocolRead, summary="Просмотреть служебный протокол")
def private_protocol(olympiad_id: Id, user: User = Depends(require_staff),
                      db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    check_owner(item, user)
    return protocol_data(db, item)


@router.patch("/olympiads/{olympiad_id}/protocol", response_model=StatusRead, summary="Подготовить, отозвать или опубликовать протокол")
def set_protocol_status(olympiad_id: Id, data: ProtocolUpdate,
                         user: User = Depends(require_staff), db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_owner(item, user)
    current = item.protocol_status
    if data.status == "published" and user.role != "admin":
        raise HTTPException(403, "Публикует только администратор")
    if (current, data.status) not in [("draft", "prepared"), ("prepared", "draft"), ("prepared", "published")]:
        raise HTTPException(409, "Недопустимый переход статуса протокола")
    if data.status == "prepared":
        if item.end_date > date.today():
            raise HTTPException(409, "Олимпиада ещё не завершена")
        counts = db.execute("""
            SELECT count(*) AS total, count(*) FILTER (WHERE score IS NULL OR result IS NULL) AS missing
            FROM participations WHERE olympiad_id = %s
            """, (item.id,)).fetchone()
        if not counts["total"] or counts["missing"]:
            raise HTTPException(409, "Укажите баллы и результат каждого участника")
    execute(db, "UPDATE olympiads SET protocol_status = %s WHERE id = %s", (data.status, item.id))
    save(db)
    item.protocol_status = data.status
    return {"status": item.protocol_status}


@router.get("/olympiads/{olympiad_id}/reports/protocol", response_class=Response, responses=REPORT_RESPONSE, summary="Скачать протокол Word или Excel")
def export_protocol(olympiad_id: Id, file_format: str = Query(default="docx", alias="format"),
                      user: User = Depends(require_staff), db: Connection = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    check_owner(item, user)
    rows = []
    for number, row in enumerate(protocol_rows(db, item.id), 1):
        rows.append([number, row["full_name"], float(row["score"]) if row["score"] is not None else "—",
                     RESULT_NAMES.get(row["result"], "Не определён")])
    title = f"Протокол: {item.title}. Статус: {item.protocol_status}"
    return make_report(title, ["№", "ФИО", "Баллы", "Результат"], rows, file_format, f"protocol_{item.id}")


@router.get("/reports/annual", response_class=Response, responses=REPORT_RESPONSE, summary="Годовой отчёт по опубликованным результатам")
def annual_report(year: int = Query(ge=2000, le=2100),
                   file_format: str = Query(default="xlsx", alias="format"),
                   user: User = Depends(require_admin), db: Connection = Depends(get_db)):
    rows = db.execute("""
        SELECT o.title, o.start_date, u.full_name, p.score, p.result
        FROM olympiads o JOIN participations p ON p.olympiad_id = o.id
        JOIN users u ON u.id = p.student_id
        WHERE EXTRACT(YEAR FROM o.start_date) = %s AND o.protocol_status = 'published'
        ORDER BY o.start_date, o.id, p.id
        """, (year,)).fetchall()
    data = [[row["title"], row["start_date"].isoformat(), row["full_name"], float(row["score"]),
             RESULT_NAMES[row["result"]]] for row in rows]
    return make_report(f"Участие студентов в олимпиадах за {year} год. Записей участия: {len(data)}",
                       ["Олимпиада", "Дата", "ФИО", "Баллы", "Результат"], data,
                       file_format, f"annual_{year}")
