
import jwt

from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError

from config import SECRET_KEY


ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


password_hasher = PasswordHasher()


def verify_password(
    password: str,
    password_hash: str
) -> bool:

    try:
        password_hasher.verify(
            password_hash,
            password
        )

        return True

    except (Argon2Error, InvalidHashError):
        # Contraseña incorrecta o hash dañado: nunca un 500
        return False


# Hash de relleno para que el login tarde lo mismo exista o no el
# usuario (si no, el tiempo de respuesta revela qué emails existen).
_DUMMY_HASH = password_hasher.hash("hashly-dummy-password")


def burn_password_check(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def create_access_token(
    user_id: int
) -> str:

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
