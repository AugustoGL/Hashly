import hashlib
import secrets

KEY_PREFIX = "hshl_live_"


def generate_key() -> tuple[str, str, str]:
    """Devuelve (key completa, prefijo visible, hash para guardar)."""

    key = KEY_PREFIX + secrets.token_urlsafe(32)

    return key, key[:14], hash_key(key)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def looks_like_api_key(token: str) -> bool:
    return token.startswith(KEY_PREFIX)
