import jwt

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import ApiKey, User

from auth.auth import SECRET_KEY, ALGORITHM
from auth.api_keys import hash_key, looks_like_api_key


security = HTTPBearer(
    description=(
        "API key (`hshl_live_...`) o token JWT obtenido en "
        "`POST /v1/users/login`."
    )
)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def _user_from_api_key(token: str, db: Session) -> User:

    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == hash_key(token))
        .first()
    )

    if api_key is None or api_key.revoked_at is not None:
        raise _unauthorized("API key inválida o revocada")

    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return api_key.user


def _user_from_jwt(token: str, db: Session) -> User:

    credentials_exception = _unauthorized(
        "Token inválido o expirado"
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:

    token = credentials.credentials

    if looks_like_api_key(token):
        return _user_from_api_key(token, db)

    return _user_from_jwt(token, db)
