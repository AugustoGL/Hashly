from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.api_keys import generate_key
from auth.dependencies import get_current_user
from database.database import get_db
from database.models import ApiKey, User


router = APIRouter(
    prefix="/keys",
    tags=["api keys"]
)


class KeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def _public(key: ApiKey) -> dict:
    return {
        "id": key.id,
        "name": key.name,
        "prefix": key.prefix,
        "created_at": key.created_at,
        "last_used_at": key.last_used_at,
        "revoked": key.revoked_at is not None
    }


@router.post("/", status_code=201)
def create_key(
    data: KeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea una API key. La key completa se muestra **una sola vez**."""

    key, prefix, key_hash = generate_key()

    api_key = ApiKey(
        user_id=current_user.id,
        name=data.name,
        prefix=prefix,
        key_hash=key_hash
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {**_public(api_key), "key": key}


@router.get("/")
def list_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keys = (
        db.query(ApiKey)
        .filter(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.id)
        .all()
    )

    return [_public(key) for key in keys]


@router.delete("/{key_id}", status_code=204)
def revoke_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    key = (
        db.query(ApiKey)
        .filter(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user.id
        )
        .first()
    )

    if key is None:
        raise HTTPException(
            status_code=404,
            detail="API key no encontrada"
        )

    if key.revoked_at is None:
        key.revoked_at = datetime.now(timezone.utc)
        db.commit()
