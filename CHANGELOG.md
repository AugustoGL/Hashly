# Changelog

## Sin publicar — revisión de seguridad

- **Dependencias:** `pypdf` 6.19.0 → 6.21.4 (15 CVE) y `pillow` 12.3.0 → 13.0.0 (1 CVE).
- **Integridad:** las imágenes multi-frame (TIFF multipágina, WebP animado) ahora incluyen todos los frames en la huella; antes solo el primero.
- **DoS:** tope de píxeles por imagen, de páginas por PDF y de tamaño del cuerpo HTTP (se corta antes de escribir a disco).
- **Rate limit:** por IP (antes se evadía inventando headers `Authorization`), con memoria acotada y límites propios para lista de espera y búsquedas públicas con archivos.
- **Sesión de la web por cookie `HttpOnly`** (antes el token vivía en `localStorage`), con protección CSRF por origen y `POST /v1/users/logout`.
- **Huellas de referencia:** un test falla si una actualización de librería cambia el hash de un PDF.
- **Cuentas:** login de tiempo constante, emails en minúsculas, hashes dañados responden 401.
- **Errores:** archivos corruptos responden 400 en vez de 500.
- **Cabeceras de seguridad** en API y web; CORS restringido a los métodos y headers usados.
- **Docker:** puertos solo en `127.0.0.1` por defecto, contenedores sin capabilities.

## v0.1.0 — 2026-11-10

Primera versión descargable.

### Sellado
- Vía gratis con OpenTimestamps sobre Bitcoin: envío a calendar servers (con nonce, en paralelo), worker que confirma pruebas y descarga pública del `.ots`.
- Vía por contrato (NFT): responde `501` "próximamente". Lista de espera real en `POST /v1/waitlist/`.
- Prueba de Merkle por archivo (`GET /v1/packages/{id}/proof/{filename}`).

### API
- Todo bajo `/v1`. Documentación OpenAPI en `/docs`.
- API keys (`hshl_live_…`, guardadas como hash, revocables) o JWT.
- Rate limit, límite de paquetes por usuario y validación de email y contraseña.
- Migraciones con Alembic, aplicadas al arrancar.
- **Privacidad:** las búsquedas públicas ya no devuelven email, nombre del paquete ni manifest.

### Web
- Landing conectada al API real (lista de espera, ejemplo de curl correcto, enlace al código).
- Entrar, panel (sellar, mis paquetes, API keys) y verificación pública.

### Instalación
- `docker compose up --build -d` (api, worker, web) o instalación manual.
- `make test` y `make smoke` (flujo completo contra el API en marcha).
- Licencia MIT.
