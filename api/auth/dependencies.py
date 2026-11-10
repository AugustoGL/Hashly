import jwt

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import ApiKey, User

from auth.auth import SECRET_KEY, ALGORITHM
from config import COOKIE_NAME, CORS_ORIGINS
from auth.api_keys import hash_key, looks_like_api_key


security = HTTPBearer(
    auto_error=False,
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


SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def _check_csrf(request: Request) -> None:
    """
    Una cookie viaja sola con cada request, así que otra página podría
    intentar usarla. Para todo lo que modifica datos se exige que el
    pedido venga de un origen permitido. (Las API keys y los JWT por
    header no necesitan esto: ninguna página ajena puede leerlos.)
    """

    if request.method in SAFE_METHODS:
        return

    if request.headers.get("origin") not in CORS_ORIGINS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origen no permitido"
        )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> User:

    # 1) Header Authorization: API key o JWT (clientes del API)
    if credentials is not None:
        token = credentials.credentials

        if looks_like_api_key(token):
            return _user_from_api_key(token, db)

        return _user_from_jwt(token, db)

    # 2) Cookie de sesión HttpOnly (la web)
    cookie = request.cookies.get(COOKIE_NAME)

    if cookie:
        _check_csrf(request)
        return _user_from_jwt(cookie, db)

    raise _unauthorized("Falta la credencial")
