# Hashly — la idea completa

Oct 20, 2026 · @Augusto

## Resumen

Hashly es un servicio de prueba de existencia e integridad de archivos: demuestra que un documento existía, sin cambios, desde una fecha determinada, sin guardar nunca el documento.

- **Problema:** contratos, actas, diseños o evidencias necesitan una fecha y una integridad que cualquiera pueda comprobar sin confiar en quien los guarda.
- **Quién lo usa:** estudios de abogados, creadores, empresas y desarrolladores que quieran integrar el sellado en su propia app mediante un API.
- **Cómo se diferencia:** el usuario elige entre dos vías independientes, una gratuita sobre Bitcoin y una paga con certificado en NFT. Los archivos originales nunca salen de su dueño.

## Cómo funciona

Cada archivo se reduce a un hash, todos los hashes se combinan en una sola raíz (merkle root) y esa raíz es lo único que se sella.

1. El usuario sube uno o más archivos. Hashly calcula el hash de cada uno y descarta el archivo.
2. Con esos hashes arma un árbol de Merkle y obtiene el `merkle_root`. Un solo valor representa todo el paquete.
3. El `merkle_root` se sella por la vía elegida (sección siguiente).
4. Para verificar, cualquiera vuelve a hashear su archivo, recalcula la raíz con la prueba de Merkle y la compara con la sellada. Si coincide, el archivo existe sin cambios desde esa fecha.

**Reglas del árbol (RFC 6962):** las hojas llevan el prefijo `0x00` y los nodos internos `0x01`, para que un nodo interno nunca pueda hacerse pasar por una hoja. El árbol se divide en potencias de dos y nunca duplica el último nodo, lo que evita que dos conjuntos distintos den la misma raíz.

La prueba de Merkle se calcula a partir del manifest (la lista de hashes por archivo), de modo que no hace falta conservar los archivos.

## Las dos vías de sellado

Son dos productos independientes, no una jerarquía: cada paquete usa una sola vía, elegida al crearlo.

|  | Vía gratis | Vía paga |
| --- | --- | --- |
| Mecanismo | OpenTimestamps sobre Bitcoin | Smart contract que mintea un NFT con el `merkle_root` |
| Red | Bitcoin, vía calendar servers | L2 (Base o Polygon) |
| Confirmación | Horas | Segundos |
| Entregable | Prueba `.ots`, auditable con cualquier cliente | Certificado NFT mostrable |
| Costo para Hashly | Casi cero (corre un worker) | Gas real, a cargo de Hashly con su wallet |
| Wallet del usuario | No necesita | Embedded wallet (Privy, Dynamic u Openfort), dueña del NFT |

**OpenTimestamps.** El paquete pasa por estados hasta confirmarse (`creating` → … → `confirmed` o `failed`). Un worker periódico actualiza la prueba con las confirmaciones de Bitcoin. La verificación completa necesita un nodo Bitcoin; sin él, la altura de bloque puede no aparecer. La integración está diseñada (ficha v2.1) pero no implementada.

**Smart contract + NFT.** El usuario final nunca firma ni paga gas. Falta decidir si el NFT es transferible o soulbound (ver decisiones abiertas).

## Arquitectura y API

&#91;embedded content: arquitectura · clientes, API, núcleo y dos vías de sellado\]

El API valida la cuenta, el núcleo calcula el `merkle_root` y cada paquete sigue una sola de las dos vías.

La regla que separa lo público de lo privado es cuán sensible es la respuesta: lo que revela datos (nombres de archivo, dueño) exige API key; lo que solo confirma existencia e integridad es público.

| Endpoint | Acceso | Motivo |
| --- | --- | --- |
| `POST /packages/` | API key | Crea el paquete a nombre de la cuenta |
| `GET /packages/` | API key | Panel "mis paquetes" |
| `GET /packages/{id}` | API key | Detalle con manifest y nombres de archivo |
| `POST /packages/search/merkle-root` | Público | Verificar por hash, sin importar qué cuenta lo creó |
| `POST /packages/search/package` | Público | Verificar subiendo los archivos |
| `GET /packages/{id}/ots-proof` | Público | El `.ots` debe poder auditarse con cualquier cliente |

**Modelo de datos.** Una cuenta de developer posee muchos paquetes. Cada paquete guarda `merkle_root`, `manifest` y `verification_method` (`ots` o `smart_contract`), y tiene como máximo un sellado asociado: `PACKAGE_TIMESTAMP` (estado, prueba OTS, confirmaciones) o `PACKAGE_CERTIFICATE` (chain, contrato, token y wallet dueña).

## Privacidad y seguridad

Hashly guarda hashes, no archivos: ni en sus servidores ni en ninguna cadena.

- **Se guarda:** el `merkle_root`, el manifest (hash y nombre de cada archivo) y la prueba de sellado.
- **No se guarda:** el contenido de los archivos.
- **Lo público confirma, no revela.** La verificación por hash responde solo si existe y cuándo se selló. Los nombres de archivo y la cuenta dueña quedan detrás de la API key.
- **Hueco a cerrar:** la búsqueda pública por `merkle_root` hoy devuelve el email del dueño. Hay que sacarlo antes de abrir el API a terceros.
- **Integridad del árbol:** prefijos de hoja y nodo distintos y sin duplicar nodos, para impedir colisiones entre conjuntos de archivos.

## Decisiones de producto

Las decisiones estructurales están cerradas; las abiertas son de producto, no de código, y las resuelve el dueño del proyecto.

**Cerradas**

- Dos vías de verificación independientes.
- Los archivos originales nunca se persisten.
- API primero: la app web es el primer cliente del propio API.
- Multi-tenancy simple: los paquetes cuelgan de la cuenta del developer (API key), sin sub-cuentas por usuario final.
- La verificación pública es global, por `merkle_root`.
- Hashly cubre el gas de la vía paga.

**Abiertas**

1. ¿El NFT es transferible (coleccionable) o soulbound, tipo ERC-5192 (prueba de autoría más fuerte)?
2. Modelo de facturación: por llamada, por paquete, por mint con margen sobre el gas, o suscripción. Probablemente cada vía tenga su propio precio.
3. Formato de `client_reference_id` y si se expone en respuestas públicas (probablemente no).
4. Límites del plan gratis, que es el gancho de adopción pero también un costo de infraestructura.

## Frontend

El frontend es una landing impactante que explica qué hace Hashly y deja a la vía por contrato anunciada como "próximamente". Es la cara pública del API y debe venderse sola: quien llegue tiene que entender el producto en menos de un minuto.

**Qué tiene que lograr**

- Un impacto visual fuerte desde el primer segundo: escena 3D con volumen, parallax y animaciones guiadas por el scroll.
- Explicar el flujo completo con una animación: archivos → hashes → árbol de Merkle → `merkle_root` → sellado.
- Una demo real en el navegador: el usuario suelta un archivo y ve su hash y el árbol, calculados localmente. El archivo nunca sale de su equipo, que es justo la promesa del producto.
- Contar las dos vías: la gratis (OpenTimestamps sobre Bitcoin) con su explicación, y la vía por contrato como bloque "próximamente" con lista de espera, sin conectar ninguna wallet.
- Sección para desarrolladores: el API, con ejemplos de código.

**Fuera de alcance por ahora:** cualquier integración web3 real (wallet, mint, NFT). Tampoco se muestran métricas, clientes ni testimonios inventados.

**Criterios de calidad:** rendimiento fluido en celular, respeto de `prefers-reduced-motion` con una versión sin movimiento, accesibilidad (contraste, teclado, lectores de pantalla) y modo claro y oscuro.

## Estado y próximos pasos

El núcleo (paquetes, manifest y Merkle) funciona; el sellado en sí, por cualquiera de las dos vías, todavía no está implementado y el proyecto está en pausa mientras la prioridad es la hackathon de Celo.

1. Cerrar las decisiones abiertas de producto.
2. Implementar la vía gratis (OpenTimestamps): está todo diseñado y es la de menor incertidumbre. Antes, confirmar contra la versión instalada de `ots` la sintaxis de hash directo y si la altura de bloque aparece sin nodo Bitcoin propio.
3. Sacar el email del dueño de la búsqueda pública por `merkle_root`.
4. Implementar la vía paga (contrato, NFT y embedded wallet), con soulbound y precios ya decididos.
5. Abrir el API a terceros: API keys y documentación al estilo Stripe.

Hay una ficha de integración de OTS (v2.1) y un documento de arquitectura y roadmap como base para retomarlo.
