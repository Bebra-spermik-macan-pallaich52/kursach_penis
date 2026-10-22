from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user_read import UserRead
from app.schemas.profile_update import ProfileUpdate
from app.schemas.password_change import PasswordChange
from app.schemas.token_read import TokenRead
from app.schemas.message_read import MessageRead
from app.security import create_token, get_current_user, hash_password, verify_password
from app.services import save

router = APIRouter(tags=["Авторизация и профиль"])


@router.post("/auth/token", response_model=TokenRead, summary="Получить JWT-токен")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash) or not user.is_active:
        raise HTTPException(401, "Неверный логин или пароль",
                            headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_token(user), "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead, summary="Посмотреть свой профиль")
def profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/users/me", response_model=UserRead, summary="Изменить свой профиль")
def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(user, name, str(value).lower() if name == "email" else value)
    save(db)
    return user


@router.put("/users/me/password", response_model=MessageRead, summary="Сменить пароль и отозвать старые токены")
def change_password(data: PasswordChange, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "Текущий пароль неверен")
    user.password_hash = hash_password(data.new_password)
    user.token_version += 1
    save(db)
    return {"message": "Пароль изменён. Войдите повторно"}


@router.delete("/auth/session", response_model=MessageRead, summary="Завершить все свои сеансы")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.token_version += 1
    save(db)
    return {"message": "Все токены пользователя отозваны"}

