# API de Hashly (v1)

Base: `http://localhost:8000/v1`. La referencia interactiva (OpenAPI) está en `/docs`.

## Autenticación

Dos formas, intercambiables, en el header `Authorization: Bearer <token>`:

- **API key** (`hshl_live_…`): para tus apps. Se crea con `POST /v1/keys/`.
- **JWT**: lo devuelve `POST /v1/users/login` (dura 60 minutos). Lo usa la web.

La API key completa se muestra **una sola vez**. Hashly guarda solo su hash.

## Público vs. privado

Lo que revela datos exige credenciales; lo que solo confirma existencia e integridad es público.

| Endpoint | Acceso |
|---|---|
| `POST /users/register`, `POST /users/login` | Público |
| `GET /users/me` | Credencial |
| `POST /keys/`, `GET /keys/`, `DELETE /keys/{id}` | Credencial |
| `POST /packages/` | Credencial |
| `GET /packages/`, `GET /packages/{id}` | Credencial (solo los tuyos) |
| `GET /packages/{id}/proof/{filename}` | Credencial |
| `POST /packages/{id}/verify` | Credencial |
| `POST /packages/search/merkle-root` | **Público** |
| `POST /packages/search/package` | **Público** |
| `GET /packages/{id}/ots-proof` | **Público** |
| `POST /waitlist/` | Público (lista de espera de la vía por contrato) |
| `GET /health` | Público |

Las respuestas públicas **no incluyen** nombre del paquete, nombres de archivo ni dueño.

## Flujo típico

### 1. Crear un paquete

```bash
curl -X POST $API/v1/packages/ -H "Authorization: Bearer $KEY" \
  -F name="Acta 14" -F files=@acta.pdf -F files=@anexo.png
```

Respuesta:

```json
{
  "id": 7,
  "name": "Acta 14",
  "created_at": "2026-11-10T14:44:44.473355",
  "merkle_root": "1c43ae74…6a72",
  "manifest": [
    { "index": 0, "filename": "acta.pdf",  "hash": "d1ba62d6…" },
    { "index": 1, "filename": "anexo.png", "hash": "02f80896…" }
  ],
  "verification_method": "ots",
  "seal": { "status": "creating", "bitcoin_block_height": null, "confirmed_at": null }
}
```

Parámetros del formulario: `name` (obligatorio), `files` (uno o más), `method` (`ots`, por defecto; `smart_contract` devuelve `501`, llega próximamente).

Formatos soportados: imágenes (`jpg`, `png`, `webp`, `bmp`, `tiff`), `pdf` y texto/código (`txt`, `md`, `py`, `js`, `ts`, `html`, `css`, `sql`, `json`, `xml`). Los archivos se normalizan antes del hash para que metadatos irrelevantes no cambien el resultado.

### 2. Estado del sello

`seal.status` avanza así: `creating` → `pending` → `confirmed` (o `failed`).

| Estado | Significado |
|---|---|
| `creating` | Enviando la raíz a los calendar servers |
| `pending` | Aceptada; esperando que Bitcoin la confirme (horas) |
| `confirmed` | Anclada en Bitcoin. `bitcoin_block_height` indica el bloque |
| `failed` | No se confirmó dentro de `OTS_MAX_PENDING_DAYS` |

### 3. Descargar la prueba `.ots`

```bash
curl -o acta.ots $API/v1/packages/7/ots-proof
```

Es pública a propósito: se puede auditar con cualquier cliente OpenTimestamps (`ots verify`). La altura de bloque que informa Hashly la reportan los calendar servers; la verificación completa necesita un nodo Bitcoin.

### 4. Verificar

Por archivos (calcula la raíz y la busca):

```bash
curl -X POST $API/v1/packages/search/package -F files=@acta.pdf -F files=@anexo.png
```

Por raíz:

```bash
curl -X POST $API/v1/packages/search/merkle-root \
  -H 'content-type: application/json' -d '{"merkle_root":"1c43ae74…6a72"}'
```

Ambas devuelven `{ "found": true|false, "merkle_root": "…", "packages": [ { "id", "created_at", "verification_method", "seal" } ] }`.

### 5. Prueba de Merkle de un archivo

```bash
curl $API/v1/packages/7/proof/anexo.png -H "Authorization: Bearer $KEY"
```

Devuelve `leaf_hash`, `merkle_root` y la lista `proof` de hermanos (`position`: `left`/`right`). Con eso se demuestra que un archivo pertenece al paquete sin revelar los demás.

**Reglas del árbol (RFC 6962):** las hojas llevan prefijo `0x00` y los nodos internos `0x01`; el subárbol izquierdo es siempre la mayor potencia de 2 menor que `n`; nunca se duplica el último nodo.

## Límites y errores

| Código | Cuándo |
|---|---|
| `400` | Archivos inválidos, duplicados, formato no soportado, raíz mal formada |
| `401` | Credencial ausente, inválida, expirada o revocada |
| `403` | Alcanzaste `MAX_PACKAGES_PER_USER` |
| `404` | No existe o no es tuyo |
| `422` | Datos mal formados (email, contraseña de menos de 8 caracteres) |
| `429` | Rate limit; mirá el header `Retry-After` |
| `501` | Vía `smart_contract` (próximamente) |

Todos los errores tienen la forma `{ "detail": "mensaje" }`.
