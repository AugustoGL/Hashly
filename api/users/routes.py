from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from argon2 import PasswordHasher

from database.database import get_db
from database.models import User

from auth.auth import verify_password, create_access_token

from auth.dependencies import get_current_user


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


password_hasher = PasswordHasher()


class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


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
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
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

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email
    }

