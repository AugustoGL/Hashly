# Hashly: landing

La cara pública de Hashly: explica el producto, deja probar el cálculo del árbol de Merkle en el navegador y anuncia la vía por contrato como "próximamente".

## Correrlo

Requiere Node 20.9 o superior.

```bash
cd web
npm install
npm run dev        # http://localhost:3000
npm run build && npm start   # producción
npm run lint
```

Variable opcional: `NEXT_PUBLIC_SITE_URL` (URL pública del sitio, para las URLs absolutas de Open Graph). Si falta, usa `http://localhost:3000`.

Parámetros de depuración de la escena: `?escena` la fuerza aunque no haya GPU, `?n=8192` baja la cantidad de partículas y `?etapa=3` arranca con esa forma armada y fija (así se generaron las imágenes de `public/stages/`).

## Cómo está hecha

- **Escena: Three.js WebGPU + TSL** ([engine.ts](src/components/scene/engine.ts)). Son 131.072 partículas (32.768 en móvil) simuladas con un compute shader. Las 7 formas de la historia ([shapes.ts](src/components/scene/shapes.ts)) se calculan una vez y viven en buffers de la GPU; el scroll fija la etapa y cada partícula viaja hacia la mezcla de dos formas con turbulencia de ruido. Se dibujan como sprites instanciados con bloom TSL. Sin WebGPU, `WebGPURenderer` cae solo a WebGL 2.
- **Huella real:** las 64 barras de la etapa "huella" son el SHA-256 de la frase del hero.
- **Hero e historia** ([Story.tsx](src/components/story/Story.tsx)): el canvas se ve primero por la ventana dentro de la frase; GSAP abre la ventana a pantalla completa y maneja las etapas con el scroll.
- **Sin GPU o con reduced motion:** no se carga Three.js; la ventana y cada paso muestran las imágenes fijas de `public/stages/`.
- **Demo** ([Showcase.tsx](src/components/sections/Showcase.tsx)): el titular es un campo de texto y su SHA-256 se recalcula en cada tecla, marcando los caracteres que cambiaron. También arma el árbol de Merkle de archivos soltados. Todo con Web Crypto.
- **Dirección de arte:** salida de la skill `design-taste-frontend` (dirección "La frase es el layout"). Tipografía Imbue para la frase grande y Albert Sans para el texto; campo navy, tinta fría y un solo acento, el ámbar de Bitcoin. Pasa su lint y su inspector con 0 fallos.

## Pendientes antes de publicar

- **Lista de espera:** `components/sections/Pricing.tsx` tiene un handler simulado (TODO). Hoy el email no se guarda en ningún lado y el usuario ve "Listo" igual.
- **Búsqueda pública:** la landing dice que la verificación por hash "confirma, no revela". El endpoint `/packages/search/merkle-root` todavía devuelve el email del dueño: hay que sacarlo antes de abrir el API.
- **Sellado:** la landing presenta la vía OpenTimestamps sin decir que ya funciona, pero el sellado todavía no está implementado en el backend.
- **API key:** el backend hoy autentica con JWT (`/users/login`). Los ejemplos usan `Authorization: Bearer $HASHLY_SECRET_KEY` y el dominio `api.hashly.example`, y están marcados como ilustrativos.
- **Email de contacto:** el footer usa `hola@hashly.app` como ejemplo. Reemplazarlo por el real.
- **Fragmentos de interfaz:** los valores de la sección "Lo que queda de tu archivo" (horas, tamaños, la secret key, el bloque confirmado) son de ejemplo.
- **Fps en un celular real:** las capturas se hicieron con una GPU emulada; falta probar la escena en dispositivos reales.
