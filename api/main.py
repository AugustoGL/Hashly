import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.ratelimit import RateLimitMiddleware
from auth.routes import router as keys_router
from config import CORS_ORIGINS
from packages.routes import router as packages_router
from users.routes import router as users_router
from waitlist.routes import router as waitlist_router


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(Path(__file__).parent / "alembic.ini"))
    cfg.set_main_option(
        "script_location", str(Path(__file__).parent / "migrations")
    )
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Los tests desactivan esto y crean las tablas por su cuenta
    if os.getenv("HASHLY_AUTO_MIGRATE", "1") != "0":
        run_migrations()
    yield


DESCRIPTION = """
Prueba de existencia e integridad de archivos.

Hashly calcula el hash de tus archivos, los combina en un árbol de Merkle
(RFC 6962) y sella la raíz en Bitcoin con OpenTimestamps. **Los archivos
originales nunca se guardan.**

**Autenticación:** `Authorization: Bearer hshl_live_...` (API key, se crea
en `POST /v1/keys`) o el JWT que devuelve `POST /v1/users/login`.

**Público:** `POST /v1/packages/search/*` y `GET /v1/packages/{id}/ots-proof`
no requieren credenciales y no revelan nombres de archivo ni dueño.
"""

app = FastAPI(
    title="Hashly API",
    version="0.1.0",
    description=DESCRIPTION,
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

v1 = APIRouter(prefix="/v1")
v1.include_router(users_router)
v1.include_router(keys_router)
v1.include_router(packages_router)
v1.include_router(waitlist_router)

app.include_router(v1)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": app.version}
