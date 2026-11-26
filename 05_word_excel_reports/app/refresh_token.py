from app.errors import log_error
from app.database import fetch_one
from fastapi import HTTPException
from app.models.user import User
from app.create_token import create_token


async def refresh_token(db, user):
    try:
        row = await fetch_one(
            db,
            """
                UPDATE users SET token_version = token_version + 1
                WHERE id = %s AND token_version = %s AND is_active = true RETURNING *
            """,
            (user.id, user.token_version),
        )
        if not row:
            raise HTTPException(401, "Токен уже обновлён. Войдите повторно")
        token = create_token(User(**row))
        await db.commit()
        return token
    except Exception as error:
        log_error(error, "refresh_token")
        raise
