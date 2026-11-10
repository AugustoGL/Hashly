"""
Middlewares ASGI de endurecimiento: tope de tamaño del cuerpo y
cabeceras de seguridad.
"""

import json

from config import MAX_TOTAL_SIZE


# Margen para los encabezados del multipart
MULTIPART_LIMIT = MAX_TOTAL_SIZE + 5 * 1024 * 1024

# JSON de login, keys, búsquedas: nunca necesitan más
DEFAULT_LIMIT = 1024 * 1024


class _BodyTooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    """
    Corta la subida apenas supera el límite, antes de que el servidor
    la vuelque a disco. Sin esto, cualquiera podría llenar el disco
    mandando un cuerpo enorme a un endpoint público.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers") or [])
        content_type = headers.get(b"content-type", b"")

        limit = (
            MULTIPART_LIMIT
            if content_type.startswith(b"multipart/")
            else DEFAULT_LIMIT
        )

        declared = headers.get(b"content-length")

        if declared is not None:
            try:
                too_large = int(declared) > limit
            except ValueError:
                too_large = True

            if too_large:
                return await self._reject(send)

        received = 0
        started = False

        async def limited_receive():
            nonlocal received

            message = await receive()

            if message["type"] == "http.request":
                received += len(message.get("body", b""))

                if received > limit:
                    raise _BodyTooLarge()

            return message

        async def tracking_send(message):
            nonlocal started

            if message["type"] == "http.response.start":
                started = True

            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not started:
                await self._reject(send)

    @staticmethod
    async def _reject(send):
        body = json.dumps(
            {"detail": "El cuerpo de la solicitud es demasiado grande"}
        ).encode()

        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"connection", b"close"),
            ],
        })

        await send({"type": "http.response.body", "body": body})


SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    # El API devuelve JSON y binarios: nunca debe ejecutar nada.
    # /docs (Swagger UI) queda exceptuado abajo.
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
    # Respuestas con tokens, keys o datos privados no se cachean
    (b"cache-control", b"no-store"),
]

DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        is_docs = scope.get("path", "").startswith(DOCS_PATHS)

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers") or [])
                present = {name.lower() for name, _ in headers}

                for name, value in SECURITY_HEADERS:
                    if is_docs and name == b"content-security-policy":
                        continue

                    if name not in present:
                        headers.append((name, value))

                message = {**message, "headers": headers}

            await send(message)

        await self.app(scope, receive, send_with_headers)
