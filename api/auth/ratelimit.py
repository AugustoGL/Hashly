"""
Rate limit en memoria (ventana deslizante de 60 s), por IP.

Se usa la IP y no el header Authorization porque ese header lo
controla el cliente: con tokens inventados se podría estrenar un
cupo nuevo en cada request.

Alcanza para una instancia única; para varias réplicas habría que
moverlo a Redis. Detrás de un proxy, configurá FORWARDED_ALLOW_IPS
para que uvicorn vea la IP real (ver docs/self-hosting.md).
"""

import time
from collections import deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import (
    AUTH_RATE_LIMIT_PER_MINUTE,
    PUBLIC_UPLOAD_RATE_LIMIT_PER_MINUTE,
    RATE_LIMIT_PER_MINUTE,
)


WINDOW = 60

# Tope de claves en memoria: evita que el propio limitador sea un DoS
MAX_KEYS = 50_000

# Endpoints sin credencial que escriben o son caros de procesar
AUTH_PATHS = (
    "/v1/users/login",
    "/v1/users/register",
    "/v1/waitlist/",
)

PUBLIC_UPLOAD_PATHS = ("/v1/packages/search/package",)


# Estado compartido del limitador (una sola instancia de la app)
HITS: dict[str, deque] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.hits = HITS

    def _prune(self, now: float) -> None:
        stale = [
            key for key, hits in self.hits.items()
            if not hits or now - hits[-1] > WINDOW
        ]

        for key in stale:
            del self.hits[key]

        # Si aun así no entra, se descarta lo más viejo
        while len(self.hits) > MAX_KEYS:
            self.hits.pop(next(iter(self.hits)))

    def _allowed(self, key: str, limit: int) -> tuple[bool, int]:
        now = time.monotonic()

        if len(self.hits) > MAX_KEYS:
            self._prune(now)

        hits = self.hits.setdefault(key, deque())

        while hits and now - hits[0] > WINDOW:
            hits.popleft()

        if len(hits) >= limit:
            return False, int(WINDOW - (now - hits[0])) + 1

        hits.append(now)
        return True, 0

    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":
            return await call_next(request)

        ip = request.client.host if request.client else "?"
        path = request.url.path

        checks = []

        if RATE_LIMIT_PER_MINUTE:
            checks.append(("all:" + ip, RATE_LIMIT_PER_MINUTE))

        if AUTH_RATE_LIMIT_PER_MINUTE and path in AUTH_PATHS:
            checks.append(("auth:" + ip, AUTH_RATE_LIMIT_PER_MINUTE))

        if (
            PUBLIC_UPLOAD_RATE_LIMIT_PER_MINUTE
            and path in PUBLIC_UPLOAD_PATHS
        ):
            checks.append(
                ("upload:" + ip, PUBLIC_UPLOAD_RATE_LIMIT_PER_MINUTE)
            )

        for key, limit in checks:
            ok, retry_after = self._allowed(key, limit)

            if not ok:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Demasiadas solicitudes. "
                                  "Probá de nuevo en unos segundos."
                    },
                    headers={"Retry-After": str(retry_after)},
                )

        return await call_next(request)
