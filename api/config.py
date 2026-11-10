import os
import secrets
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _load_secret_key() -> str:
    """
    SECRET_KEY desde el entorno. Si falta, se genera una vez y se
    guarda en data/secret_key para que los tokens sobrevivan reinicios.
    """

    value = os.getenv("SECRET_KEY")

    if value:
        return value

    path = Path(__file__).parent / "data" / "secret_key"

    if path.exists():
        return path.read_text().strip()

    path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_hex(32)
    path.write_text(value)
    path.chmod(0o600)

    return value


SECRET_KEY = _load_secret_key()


MAX_FILES = int(os.getenv("MAX_FILES", 100))

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))

MAX_TOTAL_SIZE = int(os.getenv("MAX_TOTAL_SIZE", 500 * 1024 * 1024))

# Límites del plan gratis (0 = sin límite)
MAX_PACKAGES_PER_USER = int(os.getenv("MAX_PACKAGES_PER_USER", 1000))

# Requests por minuto por cliente (0 = desactivado)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 120))

# Intentos de login/registro por minuto por IP (0 = desactivado)
AUTH_RATE_LIMIT_PER_MINUTE = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", 10))

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000"
    ).split(",")
    if origin.strip()
]

# Calendar servers de OpenTimestamps
OTS_CALENDARS = [
    url.strip()
    for url in os.getenv(
        "OTS_CALENDARS",
        "https://alice.btc.calendar.opentimestamps.org,"
        "https://bob.btc.calendar.opentimestamps.org,"
        "https://finney.calendar.eternitywall.com",
    ).split(",")
    if url.strip()
]

# Cada cuántos segundos el worker revisa los sellos pendientes
OTS_WORKER_INTERVAL = int(os.getenv("OTS_WORKER_INTERVAL", 600))

# Tras estos días sin confirmar, el sello se marca como failed
OTS_MAX_PENDING_DAYS = int(os.getenv("OTS_MAX_PENDING_DAYS", 7))
