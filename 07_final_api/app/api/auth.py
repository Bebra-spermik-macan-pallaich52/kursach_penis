from app.errors import log_error
from app.database import fetch_one
import asyncio
import re
from app.schemas.api_model import has_invalid_text
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection
from app.database import get_db, execute
from app.models.user import User
from app.schemas.user_read import UserRead
from app.schemas.profile_update import ProfileUpdate
from app.schemas.password_change import PasswordChange
from app.schemas.token_read import TokenRead
from app.schemas.message_read import MessageRead
from app.security import get_current_user, hash_password, verify_password
from app.create_token import create_token
from app.refresh_token import refresh_token
from app.records import update_fields
from app.services import get_user, save

router = APIRouter(tags=["Авторизация и профиль"])


@router.post("/auth/token", response_model=TokenRead, summary="Получить JWT-токен")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncConnection = Depends(get_db)):
    try:
        if (
            not re.fullmatch("[a-zA-Z0-9_]{3,50}", form.username)
            or not 1 <= len(form.password) <= 128
            or has_invalid_text(form.password)
        ):
            raise HTTPException(401, "Неверный логин или пароль")
        row = await fetch_one(db, "SELECT * FROM users WHERE username = %s", (form.username,))
        user = User(**row) if row else None
        if (
            not user
            or not user.is_active
            or (not await asyncio.to_thread(verify_password, form.password, user.password_hash))
        ):
            raise HTTPException(
                401, "Неверный логин или пароль", headers={"WWW-Authenticate": "Bearer"}
            )
        return {"access_token": create_token(user), "token_type": "bearer"}
    except Exception as error:
        log_error(error, "login")
        raise


@router.post("/auth/refresh", response_model=TokenRead, summary="Обновить действующий JWT-токен")
async def renew_token(
    user: User = Depends(get_current_user), db: AsyncConnection = Depends(get_db)
):
    try:
        return {"access_token": await refresh_token(db, user), "token_type": "bearer"}
    except Exception as error:
        log_error(error, "renew_token")
        raise


@router.get("/users/me", response_model=UserRead, summary="Посмотреть свой профиль")
async def profile(user: User = Depends(get_current_user)):
    try:
        return user
    except Exception as error:
        log_error(error, "profile")
        raise


@router.patch("/users/me", response_model=UserRead, summary="Изменить свой профиль")
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    try:
        values = data.model_dump(exclude_unset=True)
        if "email" in values:
            values["email"] = str(values["email"]).lower()
        await update_fields(db, "users", user.id, values)
        await save(db)
        return await get_user(db, user.id)
    except Exception as error:
        log_error(error, "update_profile")
        raise


@router.put(
    "/users/me/password",
    response_model=MessageRead,
    summary="Сменить пароль и отозвать старые токены",
)
async def change_password(
    data: PasswordChange,
    user: User = Depends(get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    try:
        if not await asyncio.to_thread(verify_password, data.old_password, user.password_hash):
            raise HTTPException(400, "Текущий пароль неверен")
        await execute(
            db,
            "UPDATE users SET password_hash = %s, token_version = token_version + 1 WHERE id = %s",
            (await asyncio.to_thread(hash_password, data.new_password), user.id),
        )
        await save(db)
        return {"message": "Пароль изменён. Войдите повторно"}
    except Exception as error:
        log_error(error, "change_password")
        raise


@router.delete("/auth/session", response_model=MessageRead, summary="Завершить все свои сеансы")
async def logout(user: User = Depends(get_current_user), db: AsyncConnection = Depends(get_db)):
    try:
        await execute(
            db, "UPDATE users SET token_version = token_version + 1 WHERE id = %s", (user.id,)
        )
        await save(db)
        return {"message": "Все токены пользователя отозваны"}
    except Exception as error:
        log_error(error, "logout")
        raise
