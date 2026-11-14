import re
from app.schemas.api_model import has_invalid_text
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import Connection
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
def login(form: OAuth2PasswordRequestForm = Depends(), db: Connection = Depends(get_db)):
    if not re.fullmatch(r"[a-zA-Z0-9_]{3,50}", form.username) or not 1 <= len(form.password) <= 128 or has_invalid_text(form.password):
        raise HTTPException(401, "Неверный логин или пароль")
    row = db.execute("SELECT * FROM users WHERE username = %s", (form.username,)).fetchone()
    user = User(**row) if row else None
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Неверный логин или пароль", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_token(user), "token_type": "bearer"}


@router.post("/auth/refresh", response_model=TokenRead, summary="Обновить действующий JWT-токен")
def renew_token(user: User = Depends(get_current_user), db: Connection = Depends(get_db)):
    return {"access_token": refresh_token(db, user), "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead, summary="Посмотреть свой профиль")
def profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/users/me", response_model=UserRead, summary="Изменить свой профиль")
def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user), db: Connection = Depends(get_db)):
    values = data.model_dump(exclude_unset=True)
    if "email" in values:
        values["email"] = str(values["email"]).lower()
    update_fields(db, "users", user.id, values)
    save(db)
    return get_user(db, user.id)


@router.put("/users/me/password", response_model=MessageRead, summary="Сменить пароль и отозвать старые токены")
def change_password(data: PasswordChange, user: User = Depends(get_current_user), db: Connection = Depends(get_db)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "Текущий пароль неверен")
    execute(db, "UPDATE users SET password_hash = %s, token_version = token_version + 1 WHERE id = %s",
            (hash_password(data.new_password), user.id))
    save(db)
    return {"message": "Пароль изменён. Войдите повторно"}


@router.delete("/auth/session", response_model=MessageRead, summary="Завершить все свои сеансы")
def logout(user: User = Depends(get_current_user), db: Connection = Depends(get_db)):
    execute(db, "UPDATE users SET token_version = token_version + 1 WHERE id = %s", (user.id,))
    save(db)
    return {"message": "Все токены пользователя отозваны"}
