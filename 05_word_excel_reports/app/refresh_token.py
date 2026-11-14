from fastapi import HTTPException
from app.database import execute
from app.models.user import User
from app.create_token import create_token


def refresh_token(db, user):
    row = execute(db, """
        UPDATE users SET token_version = token_version + 1
        WHERE id = %s AND token_version = %s AND is_active = true RETURNING *
        """, (user.id, user.token_version)).fetchone()
    if not row:
        raise HTTPException(401, "Токен уже обновлён. Войдите повторно")
    token = create_token(User(**row))
    db.commit()
    return token
