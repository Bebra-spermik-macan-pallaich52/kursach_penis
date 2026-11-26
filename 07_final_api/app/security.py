from app.errors import log_error
from app.database import fetch_one
import hashlib
import hmac
import secrets
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from psycopg import AsyncConnection
from app.config import JWT_SECRET
from app.database import get_db
from app.models.user import User

oauth2 = OAuth2PasswordBearer(tokenUrl="auth/token")


def hash_password(password):
    try:
        salt = secrets.token_hex(16)
        value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000)
        return f"pbkdf2_sha256${salt}${value.hex()}"
    except Exception as error:
        log_error(error, "hash_password")
        raise


def verify_password(password, stored):
    try:
        method, salt, expected = stored.split("$")
        if method != "pbkdf2_sha256":
            return False
        value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000)
        return hmac.compare_digest(value.hex(), expected)
    except (ValueError, TypeError):
        return False


async def get_current_user(token: str = Depends(oauth2), db: AsyncConnection = Depends(get_db)):
    try:
        error = HTTPException(
            401, "Войдите в систему повторно", headers={"WWW-Authenticate": "Bearer"}
        )
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"],
                options={"require": ["sub", "exp", "iat", "ver"]},
            )
            row = await fetch_one(db, "SELECT * FROM users WHERE id = %s", (int(payload["sub"]),))
            user = User(**row) if row else None
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            raise error
        if (
            type(payload["ver"]) is not int
            or not user
            or (not user.is_active)
            or (payload["ver"] != user.token_version)
        ):
            raise error
        return user
    except Exception as error:
        log_error(error, "get_current_user")
        raise


async def require_staff(user: User = Depends(get_current_user)):
    try:
        if user.role not in ("admin", "teacher"):
            raise HTTPException(403, "Нужны права преподавателя или администратора")
        return user
    except Exception as error:
        log_error(error, "require_staff")
        raise


async def require_admin(user: User = Depends(get_current_user)):
    try:
        if user.role != "admin":
            raise HTTPException(403, "Нужны права администратора")
        return user
    except Exception as error:
        log_error(error, "require_admin")
        raise
