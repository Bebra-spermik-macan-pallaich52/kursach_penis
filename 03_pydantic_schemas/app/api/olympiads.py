from app.errors import log_error
from app.database import fetch_all
from app.schemas.olympiad_create import OlympiadCreate
from app.schemas.olympiad_update import OlympiadUpdate
from app.schemas.olympiad_read import OlympiadRead
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import AsyncConnection
from app.database import get_db, execute
from app.models.olympiad import Olympiad
from app.services import save, get_olympiad, check_teacher
from app.records import insert_olympiad, update_fields
from app.validation import Id

router = APIRouter()


@router.get("/olympiads", response_model=list[OlympiadRead])
async def list_olympiads(
    year: int | None = Query(default=None, ge=2000, le=2100), db: AsyncConnection = Depends(get_db)
):
    try:
        if year is not None:
            return await fetch_all(
                db,
                "SELECT * FROM olympiads WHERE EXTRACT(YEAR FROM start_date) = %s ORDER BY id",
                (year,),
            )
        return await fetch_all(db, "SELECT * FROM olympiads ORDER BY id")
    except Exception as error:
        log_error(error, "olympiads")
        raise


@router.get("/olympiads/{olympiad_id}", response_model=OlympiadRead)
async def olympiad_detail(olympiad_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        return await get_olympiad(db, olympiad_id)
    except Exception as error:
        log_error(error, "olympiad")
        raise


@router.post("/olympiads", status_code=201, response_model=OlympiadRead)
async def create_olympiad(data: OlympiadCreate, db: AsyncConnection = Depends(get_db)):
    try:
        values = data.model_dump()
        await check_teacher(db, values["teacher_id"])
        item = Olympiad(**values)
        await insert_olympiad(db, item)
        await save(db)
        return item
    except Exception as error:
        log_error(error, "create_olympiad")
        raise


@router.patch("/olympiads/{olympiad_id}", response_model=OlympiadRead)
async def update_olympiad(
    olympiad_id: Id, data: OlympiadUpdate, db: AsyncConnection = Depends(get_db)
):
    try:
        item = await get_olympiad(db, olympiad_id)
        values = data.model_dump(exclude_unset=True)
        if "teacher_id" in values:
            await check_teacher(db, values["teacher_id"])
        if values.get("end_date", item.end_date) < values.get("start_date", item.start_date):
            raise HTTPException(422, "Неверный порядок дат")
        for name, value in values.items():
            setattr(item, name, value)
        await update_fields(db, "olympiads", item.id, values)
        await save(db)
        return item
    except Exception as error:
        log_error(error, "update_olympiad")
        raise


@router.delete("/olympiads/{olympiad_id}", status_code=204)
async def delete_olympiad(olympiad_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        item = await get_olympiad(db, olympiad_id)
        await execute(db, "DELETE FROM olympiads WHERE id = %s", (item.id,))
        await save(db)
    except Exception as error:
        log_error(error, "delete_olympiad")
        raise
