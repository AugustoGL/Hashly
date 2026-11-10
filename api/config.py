
import os

from dotenv import load_dotenv


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY no está configurada"
    )


MAX_FILES = int(
    os.getenv("MAX_FILES", 100)
)

MAX_FILE_SIZE = int(
    os.getenv(
        "MAX_FILE_SIZE",
        50 * 1024 * 1024
    )
)

MAX_TOTAL_SIZE = int(
    os.getenv(
        "MAX_TOTAL_SIZE",
        500 * 1024 * 1024
    )
)
