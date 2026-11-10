# Changelog

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
