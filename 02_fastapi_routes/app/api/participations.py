from app.errors import log_error
from app.database import fetch_all, fetch_one
from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from app.database import get_db
from app.models.user import User
from app.models.participation import Participation
from app.services import save, get_olympiad
from app.records import insert_participation
from app.validation import Id
from app.services import participation_data

router = APIRouter()


@router.post("/olympiads/{olympiad_id}/participants/{student_id}", status_code=201)
async def enroll(olympiad_id: Id, student_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        await get_olympiad(db, olympiad_id)
        row = await fetch_one(db, "SELECT * FROM users WHERE id = %s", (student_id,))
        student = User(**row) if row else None
        if not student or student.role != "student" or (not student.is_active):
            raise HTTPException(422, "Нужен действующий студент")
        part = Participation(olympiad_id=olympiad_id, student_id=student_id)
        await insert_participation(db, part)
        await save(db)
        return participation_data(part, student)
    except Exception as error:
        log_error(error, "enroll")
        raise


@router.get("/olympiads/{olympiad_id}/participants")
async def list_participants(olympiad_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        await get_olympiad(db, olympiad_id)
        return await fetch_all(
            db,
            """
                SELECT p.*, u.full_name FROM participations p JOIN users u ON u.id = p.student_id
                WHERE p.olympiad_id = %s ORDER BY p.id
            """,
            (olympiad_id,),
        )
    except Exception as error:
        log_error(error, "participants")
        raise
