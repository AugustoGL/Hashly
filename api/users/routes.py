from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from argon2 import PasswordHasher

from database.database import get_db
from database.models import User

from auth.auth import (
    burn_password_check,
    create_access_token,
    verify_password,
)

from auth.auth import ACCESS_TOKEN_EXPIRE_MINUTES
from auth.dependencies import get_current_user
from config import COOKIE_NAME, COOKIE_SAMESITE, COOKIE_SECURE


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


password_hasher = PasswordHasher()


def _normalize_email(value):
    # Un solo usuario por email, sin importar mayúsculas
    return value.strip().lower() if isinstance(value, str) else value


class UserCreate(BaseModel):
    email: str = Field(
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )
    password: str = Field(min_length=8, max_length=128)

    _email = field_validator("email", mode="before")(_normalize_email)


class UserLogin(BaseModel):
    email: str = Field(max_length=255)
    # Tope de largo: argon2 con contraseñas enormes es un DoS barato
    password: str = Field(max_length=128)

    _email = field_validator("email", mode="before")(_normalize_email)


def _cookie_secure(request: Request) -> bool:
    if COOKIE_SECURE == "auto":
        # SameSite=None exige Secure sí o sí
        return request.url.scheme == "https" or COOKIE_SAMESITE == "none"

    return COOKIE_SECURE in ("1", "true", "yes")


@router.post("/register")
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )

    password_hash = password_hasher.hash(
        user_data.password
    )

    user = User(
        email=user_data.email,
        password_hash=password_hash
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }


@router.post("/login")
def login_user(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Devuelve un JWT (para usar por header) y además deja una cookie de
    sesión `HttpOnly`, que es la que usa la web: el JavaScript de la
    página no puede leerla.
    """

    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
        burn_password_check(user_data.password)

        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos"
        )

    if not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos"
        )

    access_token = create_access_token(
        user.id
    )

    response.set_cookie(
        COOKIE_NAME,
        access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=_cookie_secure(request),
        samesite=COOKIE_SAMESITE,
        path="/"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout", status_code=204)
def logout_user(request: Request, response: Response):
    """Borra la cookie de sesión de la web."""

    response.delete_cookie(
        COOKIE_NAME,
        httponly=True,
        secure=_cookie_secure(request),
        samesite=COOKIE_SAMESITE,
        path="/"
    )

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email
    }

