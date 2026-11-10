"""
Cliente OpenTimestamps: sella un digest en los calendar servers y
mejora (upgrade) la prueba cuando Bitcoin la confirma.

Todo el acceso a red está acá, así los tests lo reemplazan fácil.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from opentimestamps.calendar import (
    CommitmentNotFoundError,
    RemoteCalendar,
    DEFAULT_CALENDAR_WHITELIST,
)
from opentimestamps.core.notary import (
    BitcoinBlockHeaderAttestation,
    PendingAttestation,
)
from opentimestamps.core.op import OpAppend, OpSHA256
from opentimestamps.core.serialize import (
    BytesDeserializationContext,
    BytesSerializationContext,
)
from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp

from config import OTS_CALENDARS


TIMEOUT = 15


class OtsError(Exception):
    pass


@dataclass
class UpgradeResult:
    proof: bytes
    confirmed: bool
    block_height: int | None


def _serialize(detached: DetachedTimestampFile) -> bytes:
    ctx = BytesSerializationContext()
    detached.serialize(ctx)
    return ctx.getbytes()


def _deserialize(proof: bytes) -> DetachedTimestampFile:
    ctx = BytesDeserializationContext(proof)
    return DetachedTimestampFile.deserialize(ctx)


def stamp(digest: bytes) -> bytes:
    """
    Sella un digest SHA-256 (32 bytes) y devuelve un .ots pendiente.
    Se agrega un nonce aleatorio para que los calendar servers nunca
    vean el digest real.
    """

    if len(digest) != 32:
        raise OtsError("El digest debe tener 32 bytes")

    detached = DetachedTimestampFile(OpSHA256(), Timestamp(digest))

    nonce = detached.timestamp.ops.add(OpAppend(os.urandom(16)))
    nonce_hash = nonce.ops.add(OpSHA256())

    def submit(url: str):
        try:
            return RemoteCalendar(url).submit(
                nonce_hash.msg, timeout=TIMEOUT
            ), None
        except Exception as error:  # red, timeouts, respuestas raras
            return None, error

    # En paralelo: cada calendar puede tardar varios segundos
    with ThreadPoolExecutor(max_workers=len(OTS_CALENDARS) or 1) as pool:
        outcomes = list(pool.map(submit, OTS_CALENDARS))

    submitted = 0
    last_error = None

    for result, error in outcomes:
        if result is not None:
            nonce_hash.merge(result)
            submitted += 1
        else:
            last_error = error

    if submitted == 0:
        raise OtsError(
            f"Ningún calendar server respondió: {last_error}"
        )

    return _serialize(detached)


def upgrade(proof: bytes) -> UpgradeResult:
    """
    Pregunta a los calendar servers si ya hay confirmación en Bitcoin
    para cada attestation pendiente y la incorpora a la prueba.
    """

    detached = _deserialize(proof)
    whitelist = DEFAULT_CALENDAR_WHITELIST

    pending = [
        (sub, att)
        for sub, att in _walk(detached.timestamp)
        if isinstance(att, PendingAttestation)
    ]

    for sub, att in pending:
        # Solo se consultan calendar servers conocidos (anti-SSRF)
        if att.uri not in whitelist and att.uri not in OTS_CALENDARS:
            continue

        try:
            upgraded = RemoteCalendar(att.uri).get_timestamp(
                sub.msg, timeout=TIMEOUT
            )
        except (CommitmentNotFoundError, Exception):
            continue

        sub.merge(upgraded)

        # Una vez confirmada en Bitcoin, la attestation pendiente sobra
        if _block_height(upgraded) is not None:
            sub.attestations.discard(att)

    height = _block_height(detached.timestamp)

    return UpgradeResult(
        proof=_serialize(detached),
        confirmed=height is not None,
        block_height=height,
    )


def _walk(timestamp: Timestamp):
    """Recorre el árbol devolviendo (sub-timestamp, attestation)."""

    for att in timestamp.attestations:
        yield timestamp, att

    for sub in timestamp.ops.values():
        yield from _walk(sub)


def _block_height(timestamp: Timestamp) -> int | None:
    heights = [
        att.height
        for _, att in _walk(timestamp)
        if isinstance(att, BitcoinBlockHeaderAttestation)
    ]

    return min(heights) if heights else None
