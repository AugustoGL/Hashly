# Seguridad

## Qué guarda Hashly

- **Sí:** la `merkle_root`, el manifest (hash y nombre de cada archivo), la prueba de sellado y los datos de tu cuenta (email y hash argon2 de la contraseña).
- **No:** el contenido de los archivos. Se hashean en memoria y se descartan.

## Lo público confirma, no revela

La verificación pública responde solo si una raíz existe y desde cuándo. Nombres de paquete, nombres de archivo y la cuenta dueña quedan detrás de una credencial.

## Credenciales

- Las API keys se guardan como SHA-256; la key completa se muestra una sola vez y se puede revocar.
- Las contraseñas usan Argon2.
- Los tokens JWT duran 60 minutos y se firman con `SECRET_KEY`.
- Login, registro y el API completo tienen rate limit.

## Calendar servers

Al sellar, Hashly envía a los calendar servers un hash con un nonce aleatorio, nunca la raíz real. Al actualizar pruebas solo consulta servidores de una lista conocida.

## Limitaciones de v0.1

- El rate limit es en memoria (una sola instancia).
- La altura de bloque la informan los calendar servers; la verificación completa requiere un nodo Bitcoin propio.
- Los JWT de la web viven en `localStorage`.

## Reportar una vulnerabilidad

Abrí un *security advisory* privado en GitHub (pestaña Security del repositorio). No publiques detalles en un issue.
