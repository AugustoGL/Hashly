"""
Ciclo de vida del sello OTS de un paquete:

    creating -> pending -> confirmed
                       (o failed si no confirma a tiempo)
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from config import OTS_MAX_PENDING_DAYS
from database.models import PackageTimestamp
from ots import client


def _now() -> datetime:
    return datetime.now(timezone.utc)


def submit(db: Session, timestamp_id: int) -> None:
    """creating -> pending: envía el merkle_root a los calendars."""

    ts = db.get(PackageTimestamp, timestamp_id)

    if ts is None or ts.status != "creating":
        return

    try:
        digest = bytes.fromhex(ts.package.merkle_root)
        ts.ots_proof = client.stamp(digest)
        ts.status = "pending"
        ts.error = None
    except Exception as error:
        # Sigue en "creating": el worker lo reintenta
        ts.error = str(error)[:500]

    ts.last_checked_at = _now()
    db.commit()


def refresh(db: Session, ts: PackageTimestamp) -> None:
    """pending -> confirmed (o failed si pasó demasiado tiempo)."""

    if ts.status != "pending" or not ts.ots_proof:
        return

    try:
        result = client.upgrade(ts.ots_proof)
    except Exception as error:
        ts.error = str(error)[:500]
        ts.last_checked_at = _now()
        db.commit()
        return

    ts.ots_proof = result.proof
    ts.last_checked_at = _now()
    ts.error = None

    if result.confirmed:
        ts.status = "confirmed"
        ts.bitcoin_block_height = result.block_height
        ts.confirmed_at = _now()
    else:
        created = ts.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        if _now() - created > timedelta(days=OTS_MAX_PENDING_DAYS):
            ts.status = "failed"
            ts.error = "Sin confirmación en Bitcoin dentro del plazo"

    db.commit()


def process_all(db: Session) -> dict:
    """Una pasada del worker. Devuelve contadores para el log."""

    submitted = refreshed = 0

    for ts in (
        db.query(PackageTimestamp)
        .filter(PackageTimestamp.status == "creating")
        .all()
    ):
        submit(db, ts.id)
        submitted += 1

    for ts in (
        db.query(PackageTimestamp)
        .filter(PackageTimestamp.status == "pending")
        .all()
    ):
        refresh(db, ts)
        refreshed += 1

    return {"submitted": submitted, "refreshed": refreshed}
