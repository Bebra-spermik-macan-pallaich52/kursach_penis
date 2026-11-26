from app.errors import log_error
import hashlib
import secrets


def hash_password(password):
    try:
        salt = secrets.token_hex(16)
        value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000)
        return f"pbkdf2_sha256${salt}${value.hex()}"
    except Exception as error:
        log_error(error, "hash_password")
        raise
