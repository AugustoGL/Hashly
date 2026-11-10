# Seguridad

## Qué guarda Hashly

- **Sí:** la `merkle_root`, el manifest (hash y nombre de cada archivo), la prueba de sellado y los datos de tu cuenta (email y hash Argon2 de la contraseña).
- **No:** el contenido de los archivos. Se hashean en memoria y se descartan.

## Lo público confirma, no revela

La verificación pública responde solo si una raíz existe y desde cuándo. Nombres de paquete, nombres de archivo y la cuenta dueña quedan detrás de una credencial.

## Credenciales

- Las API keys se guardan como SHA-256; la key completa se muestra una sola vez y se puede revocar.
- Las contraseñas usan Argon2. El login tarda lo mismo exista o no el usuario.
- Los tokens JWT duran 60 minutos y se firman con `SECRET_KEY` (HS256, algoritmo fijo).
- Los emails se normalizan a minúsculas: una sola cuenta por dirección.

## Protecciones contra abuso

- **Rate limit por IP:** general, más estricto en login, registro y lista de espera, y otro para las búsquedas públicas con archivos.
- **Tope de tamaño del cuerpo:** la subida se corta apenas supera el límite, antes de tocar el disco.
- **Archivos hostiles:** tope de píxeles por imagen (bombas de descompresión), tope de páginas por PDF, y cualquier archivo corrupto se responde con `400`, nunca con un error interno.
- **Cabeceras:** `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy` y `Cache-Control: no-store` en el API; CSP y equivalentes en la web.
- **Docker:** contenedores sin root, sin capabilities y con `no-new-privileges`. Los puertos escuchan solo en `127.0.0.1` salvo que lo cambies.

## Calendar servers

Al sellar, Hashly envía a los calendar servers un hash con un nonce aleatorio, nunca la raíz real. Al actualizar pruebas solo consulta servidores de una lista conocida.

## Qué cubre exactamente la huella de un archivo

Hashly normaliza cada archivo antes de hashearlo, para que cambios irrelevantes no rompan la verificación. Eso define qué queda protegido:

- **Texto y código:** el contenido completo (solo se unifican los saltos de línea).
- **Imágenes:** los píxeles de **todos** los frames. Los metadatos (EXIF, etc.) no forman parte de la huella.
- **PDF:** el contenido de las páginas. Elementos a nivel documento (metadatos, adjuntos incrustados, JavaScript, formularios) **no** forman parte de la huella. Si necesitás cubrir el PDF byte a byte, agregá al mismo paquete un `.txt` con el SHA-256 del archivo original.

## Limitaciones conocidas

- El rate limit es en memoria (una sola instancia) y por IP. Detrás de un proxy hay que configurar `FORWARDED_ALLOW_IPS` (ver `docs/self-hosting.md`).
- `GET /v1/packages/{id}/ots-proof` es público y los ids son correlativos: cualquiera puede descargar las pruebas y, con ellas, las raíces. No revela nombres, archivos ni dueños, pero sí cuántos paquetes hay y cuándo se sellaron.
- El registro informa si un email ya está en uso.
- Los JWT de la web viven en `localStorage`; no hay revocación antes de su vencimiento.
- La huella de un PDF depende de cómo lo reescribe la librería `pypdf`: una actualización futura podría cambiarla. Por eso su versión está fijada.
- La altura de bloque la informan los calendar servers; la verificación completa requiere un nodo Bitcoin propio.

## Reportar una vulnerabilidad

Abrí un *security advisory* privado en GitHub (pestaña Security del repositorio). No publiques detalles en un issue.
