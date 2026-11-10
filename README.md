# Hashly

**Prueba de existencia e integridad de archivos.** Demostrá que un documento existía, sin cambios, desde una fecha determinada, sin guardar nunca el documento.

Cada archivo se reduce a un hash, todos los hashes se combinan en un árbol de Merkle ([RFC 6962](https://datatracker.ietf.org/doc/html/rfc6962)) y la raíz se sella en Bitcoin con [OpenTimestamps](https://opentimestamps.org). Cualquiera puede verificar el sello con cualquier cliente OpenTimestamps, sin confiar en Hashly.

- **API primero:** la web es solo el primer cliente del mismo API público.
- **Se instala en tu máquina:** un `docker compose up` y listo. Sin cuentas externas.
- **Privado por diseño:** se guarda el hash, el manifest y la prueba. Nunca el contenido de los archivos.

> **Estado: v0.1.** Vía gratis (Bitcoin / OpenTimestamps) funcionando. La vía paga con certificado NFT llega próximamente.

## Instalación rápida (Docker)

```bash
git clone https://github.com/AugustoGL/hashly.git
cd hashly
cp .env.example .env
docker compose up --build -d
```

| Qué | Dónde |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| Documentación interactiva del API | http://localhost:8000/docs |

Creá una cuenta en la web, sellá tus archivos y listo. Los sellos se confirman en Bitcoin en unas horas; el servicio `worker` los actualiza solo.

¿Un puerto ocupado? Ver [docs/self-hosting.md](docs/self-hosting.md).

## Instalación sin Docker

Necesitás Python 3.12+ y Node 22+.

```bash
# API
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000        # crea las tablas solo (Alembic)

# Worker de sellado (otra terminal, mismo venv)
python worker.py

# Web (otra terminal)
cd web
npm install
npm run dev
```

## Probarlo con curl

```bash
# 1) Cuenta y token
curl -X POST localhost:8000/v1/users/register -H 'content-type: application/json' \
  -d '{"email":"yo@ejemplo.com","password":"una-clave-larga"}'
TOKEN=$(curl -s -X POST localhost:8000/v1/users/login -H 'content-type: application/json' \
  -d '{"email":"yo@ejemplo.com","password":"una-clave-larga"}' | jq -r .access_token)

# 2) API key para tu app
curl -X POST localhost:8000/v1/keys/ -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' -d '{"name":"mi-app"}'
# => { "key": "hshl_live_..." }   (se muestra una sola vez)

# 3) Sellar archivos
curl -X POST localhost:8000/v1/packages/ -H "authorization: Bearer hshl_live_..." \
  -F name="Contrato" -F files=@contrato.pdf -F files=@anexo.pdf

# 4) Verificar (público, sin credenciales)
curl -X POST localhost:8000/v1/packages/search/package \
  -F files=@contrato.pdf -F files=@anexo.pdf
```

Más en [docs/api.md](docs/api.md).

## Cómo funciona

1. Subís uno o más archivos. Hashly calcula el hash de cada uno y descarta el archivo.
2. Con esos hashes arma un árbol de Merkle y obtiene la `merkle_root`: un solo valor para todo el paquete.
3. La raíz se envía a los calendar servers de OpenTimestamps, que la anclan en Bitcoin.
4. Para verificar, cualquiera vuelve a hashear sus archivos, recalcula la raíz y la compara con la sellada.

Detalle completo en [docs/idea.md](docs/idea.md).

## Estructura

```
api/    Backend FastAPI (núcleo Merkle, API, worker OpenTimestamps, migraciones)
web/    Landing y app (Next.js)
docs/   Documentación
```

## Desarrollo

```bash
make test         # tests del backend (no usan la red)
```

## Qué viene

- Vía paga: certificado NFT en un L2 (Base o Polygon), con wallet embebida.
- Verificación local del `.ots` contra un nodo Bitcoin propio.

## Licencia

[MIT](LICENSE)
