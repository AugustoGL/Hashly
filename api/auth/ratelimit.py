"""
Rate limit en memoria (ventana deslizante de 60 s).
Alcanza para una instancia única; para varias réplicas habría que
moverlo a Redis.
"""

import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import RATE_LIMIT_PER_MINUTE, AUTH_RATE_LIMIT_PER_MINUTE


WINDOW = 60

AUTH_PATHS = ("/v1/users/login", "/v1/users/register")


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.hits: dict[str, deque] = defaultdict(deque)

    def _client_id(self, request: Request) -> str:
        auth = request.headers.get("authorization", "")

        if auth:
            return "tok:" + auth[-24:]

        return "ip:" + (request.client.host if request.client else "?")

    def _allowed(self, key: str, limit: int) -> tuple[bool, int]:
        now = time.monotonic()
        hits = self.hits[key]

        while hits and now - hits[0] > WINDOW:
            hits.popleft()

        if len(hits) >= limit:
            return False, int(WINDOW - (now - hits[0])) + 1

        hits.append(now)
        return True, 0

    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":
            return await call_next(request)

        checks = []

        if RATE_LIMIT_PER_MINUTE:
            checks.append(
                (self._client_id(request), RATE_LIMIT_PER_MINUTE)
            )

        if AUTH_RATE_LIMIT_PER_MINUTE and request.url.path in AUTH_PATHS:
            ip = request.client.host if request.client else "?"
            checks.append(("auth:" + ip, AUTH_RATE_LIMIT_PER_MINUTE))

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
