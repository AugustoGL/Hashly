# Self-hosting

## Requisitos

Docker con Compose v2, o bien Python 3.12+ y Node 22+.

## Servicios

| Servicio | Puerto | Qué hace |
|---|---|---|
| `api` | 8000 | API FastAPI. Aplica las migraciones al arrancar |
| `worker` | — | Reintenta envíos y confirma pruebas OTS cada `OTS_WORKER_INTERVAL` s |
| `web` | 3000 | Landing y app |

Los datos viven en el volumen `hashly-data` (SQLite + clave secreta autogenerada).

## Configuración

Todo se configura con variables de entorno (archivo `.env`, ver `.env.example`).

| Variable | Por defecto | Para qué |
|---|---|---|
| `SECRET_KEY` | autogenerada | Firma de tokens. Si la fijás, usá 32+ bytes |
| `DATABASE_URL` | SQLite en `/app/data` | Postgres opcional |
| `CORS_ORIGINS` | `http://localhost:3000` | Orígenes del navegador permitidos |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL del API **vista desde el navegador** (se incrusta al construir la web) |
| `MAX_FILES` / `MAX_FILE_SIZE` / `MAX_TOTAL_SIZE` | 100 / 50 MB / 500 MB | Límites de subida |
| `MAX_PACKAGES_PER_USER` | 1000 | Plan gratis (0 = sin límite) |
| `RATE_LIMIT_PER_MINUTE` | 120 | Por cliente (0 = apagado) |
| `AUTH_RATE_LIMIT_PER_MINUTE` | 10 | Login/registro por IP |
| `OTS_CALENDARS` | alice, bob, finney | Calendar servers de OpenTimestamps |
| `OTS_WORKER_INTERVAL` | 600 | Segundos entre pasadas del worker |
| `OTS_MAX_PENDING_DAYS` | 7 | Días antes de marcar un sello como `failed` |

## Cambiar de puerto

Si el 3000 u 8000 están ocupados, en `.env` poné por ejemplo:

```
WEB_PORT=3100
API_PORT=8100
CORS_ORIGINS=http://localhost:3100
NEXT_PUBLIC_API_URL=http://localhost:8100
```

## Publicarlo en un servidor

1. Poné un proxy con HTTPS delante (Caddy, Nginx, Traefik) para web y API.
2. En `.env`: `CORS_ORIGINS=https://tu-dominio.com` y `NEXT_PUBLIC_API_URL=https://api.tu-dominio.com`.
3. `docker compose up --build -d` (la URL del API se incrusta al construir la web, así que hay que reconstruir al cambiarla).
4. Si vas a tener muchos usuarios, usá Postgres y no corras varias réplicas del API: el rate limit es en memoria.

## Postgres

```bash
# api/requirements.txt
psycopg[binary]==3.2.*
# .env
DATABASE_URL=postgresql+psycopg://usuario:clave@host:5432/hashly
```

Las migraciones (Alembic) funcionan igual.

## Backups

Todo el estado está en la base de datos. Con SQLite:

```bash
docker compose exec api python -c "import sqlite3; s=sqlite3.connect('/app/data/hashly.db'); d=sqlite3.connect('/app/data/backup.db'); s.backup(d)"
docker compose cp api:/app/data/backup.db ./backup.db
```

Guardá también el `.ots` de los paquetes importantes: es tu prueba, y se puede verificar sin Hashly.

## Actualizar

```bash
git pull
docker compose up --build -d     # las migraciones se aplican solas
```

## Problemas comunes

- **La web dice "No se pudo conectar con el API":** revisá `NEXT_PUBLIC_API_URL` y `CORS_ORIGINS`.
- **Un sello sigue en `pending`:** es normal por unas horas. Mirá `docker compose logs worker`.
- **Error de migración con una base vieja:** si venís de un prototipo anterior sin Alembic, borrá `data/hashly.db`.
