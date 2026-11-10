
import jwt

from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

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

    except VerifyMismatchError:
        return False


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
