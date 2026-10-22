"""Пароли хранятся в виде PBKDF2-хеша с отдельной солью."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import JWT_SECRET, get_db
from app.models import User

TOKEN_MINUTES = 60
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/token")


def hash_password(password):
    salt = secrets.token_hex(16)
    value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000)
    return f"pbkdf2_sha256${salt}${value.hex()}"


def verify_password(password, stored):
    try:
        method, salt, expected = stored.split("$")
        if method != "pbkdf2_sha256":
            return False
        value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000)
        return hmac.compare_digest(value.hex(), expected)
    except (ValueError, TypeError):
        return False


def create_token(user):
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user.id), "ver": user.token_version,
                       "iat": now, "exp": now + timedelta(minutes=TOKEN_MINUTES)},
                      JWT_SECRET, algorithm="HS256")


def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    error = HTTPException(401, "Войдите в систему повторно",
                          headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"],
                             options={"require": ["sub", "exp", "iat", "ver"]})
        user = db.get(User, int(payload["sub"]))
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise error
    if not user or not user.is_active or payload["ver"] != user.token_version:
        raise error
    return user


def require_staff(user: User = Depends(get_current_user)):
    if user.role not in ("admin", "teacher"):
        raise HTTPException(403, "Нужны права преподавателя или администратора")
    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Нужны права администратора")
    return user

