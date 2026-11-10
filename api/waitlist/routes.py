from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import WaitlistEntry


router = APIRouter(
    prefix="/waitlist",
    tags=["waitlist"]
)


class WaitlistJoin(BaseModel):
    email: str = Field(
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )
    interest: Literal["contrato", "bitcoin"] = "contrato"

    @field_validator("email", mode="before")
    @classmethod
    def _normalize(cls, value):
        return value.strip() if isinstance(value, str) else value


@router.post("/", status_code=201)
def join_waitlist(
    data: WaitlistJoin,
    db: Session = Depends(get_db)
):
    """
    Lista de espera de la vía por contrato (NFT), que llega próximamente.
    Anotarse dos veces con el mismo email no duplica la entrada.
    """

    email = data.email.strip().lower()

    exists = (
        db.query(WaitlistEntry)
        .filter(
            WaitlistEntry.email == email,
            WaitlistEntry.interest == data.interest
        )
        .first()
    )

    if exists is None:
        db.add(WaitlistEntry(email=email, interest=data.interest))
        db.commit()

    # La respuesta no revela si el email ya estaba anotado
    return {"ok": True}
