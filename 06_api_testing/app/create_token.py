from app.errors import log_error
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from app.config import JWT_SECRET, TOKEN_MINUTES


def create_token(user):
    try:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": str(user.id),
                "ver": user.token_version,
                "iat": now,
                "exp": now + timedelta(minutes=TOKEN_MINUTES),
                "jti": uuid4().hex,
            },
            JWT_SECRET,
            algorithm="HS256",
        )
    except Exception as error:
        log_error(error, "create_token")
        raise
