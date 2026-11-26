from app.errors import log_error
from app.database import fetch_all
import asyncio
from fastapi import APIRouter, Depends
from psycopg import AsyncConnection
from app.database import get_db
from app.models.user import User
from app.security import hash_password
from app.services import save
from app.records import insert_user
from app.services import user_data
from app.validation import read_user

router = APIRouter()


@router.get("/users")
async def list_users(db: AsyncConnection = Depends(get_db)):
    try:
        return [
            user_data(User(**row)) for row in await fetch_all(db, "SELECT * FROM users ORDER BY id")
        ]
    except Exception as error:
        log_error(error, "users")
        raise


@router.post("/users", status_code=201)
async def create_user(data: dict, db: AsyncConnection = Depends(get_db)):
    try:
        values = read_user(data)
        password = values.pop("password")
        user = User(**values, password_hash=await asyncio.to_thread(hash_password, password))
        await insert_user(db, user)
        await save(db)
        return user_data(user)
    except Exception as error:
        log_error(error, "create_user")
        raise
