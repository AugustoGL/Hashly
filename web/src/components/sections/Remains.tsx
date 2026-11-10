import { highlight } from "@/lib/highlight";

/**
 * "Lo que queda de tu archivo": filas colgadas de un eje, cada una con un fragmento
 * de la interfaz del producto al margen. Los valores de los fragmentos son de ejemplo.
 */

const manifest = `{
  "merkle_root": "9e41c07a5bd2…6b8a1d4f",
  "manifest": [
    { "index": 0, "filename": "anexo.pdf",
      "hash": "3f9a8e12…c21e" },
    { "index": 1, "filename": "contrato.pdf",
      "hash": "a41f6b0d…079c" }
  ]
}`;

const apiCall = `curl http://localhost:8000/v1/packages/ \\
  -H "Authorization: Bearer $HASHLY_API_KEY" \\
  -F "name=Contrato de locación" \\
  -F "files=@contrato.pdf"`;

function Fragment({ children, className, label }: { children: React.ReactNode; className: string; label: string }) {
  return (
    <figure data-ui aria-label={label} className={`shrink-0 overflow-hidden rounded-[6px] bg-surface ${className}`}>
      {children}
    </figure>
  );
}

export async function Remains() {
  const [manifestHtml, apiHtml] = await Promise.all([highlight(manifest, "json"), highlight(apiCall, "bash")]);

  const rows: { id?: string; title: string; body: string; fragment: React.ReactNode }[] = [
    {
      title: "Tu archivo, en ningún disco",
      body: "Hashly lo procesa en memoria para calcular su hash y lo descarta. No queda en nuestros servidores ni en ninguna cadena.",
      fragment: (
        <Fragment label="Registro de procesamiento de un archivo, de ejemplo" className="w-full sm:w-[240px] aspect-[4/5] p-5 text-[0.8125rem]">
          <p className="text-muted">contrato.pdf</p>
          <code className="block mt-1 text-ink">2,4 MB</code>
          <ol className="mt-6 space-y-4">
            <li>
              <span className="text-muted">Recibido</span>
              <code className="block text-ink">14:03:11.204</code>
            </li>
            <li>
              <span className="text-muted">Hash calculado</span>
              <code className="block text-ink">a41f6b0d…079c</code>
            </li>
            <li>
              <span className="text-muted">Archivo descartado</span>
              <code className="block text-ok">0 bytes guardados</code>
            </li>
          </ol>
        </Fragment>
      ),
    },
    {
      title: "Se guardan nombres y huellas",
      body: "Queda un manifest con el nombre y el hash de cada archivo, más la raíz. Con eso alcanza para calcular la prueba de cualquiera de ellos.",
      fragment: (
        <Fragment label="Manifest de un paquete, de ejemplo" className="w-full sm:w-[340px] aspect-[3/2]">
          <div className="code-block text-[0.75rem]" dangerouslySetInnerHTML={{ __html: manifestHtml }} />
        </Fragment>
      ),
    },
    {
      title: "En Bitcoin, 32 bytes",
      body: "Lo único que llega a la cadena es la raíz, agregada por OpenTimestamps junto a otras. De 32 bytes no se reconstruye ningún archivo.",
      fragment: (
        <Fragment label="Estado del sello de un paquete, de ejemplo" className="w-full sm:w-[200px] aspect-square p-5 text-[0.8125rem]">
          <p className="text-muted">Sello en Bitcoin</p>
          <p className="mt-3 font-medium text-accent">Confirmado</p>
          <p className="mt-4 text-muted">merkle_root</p>
          <code className="block text-ink">9e41c07a…</code>
          <p className="mt-4 text-muted">Confirmaciones</p>
          <code className="block text-ink">6</code>
        </Fragment>
      ),
    },
    {
      title: "Una prueba que es tuya",
      body: "Descargás un archivo .ots y lo verificás con cualquier cliente de OpenTimestamps, aunque Hashly deje de existir.",
      fragment: (
        <Fragment label="Prueba .ots descargable, de ejemplo" className="w-full sm:w-[260px] aspect-[4/5] p-5 text-[0.8125rem]">
          <div className="grid aspect-[3/4] w-24 place-items-center rounded-[4px] bg-surface-2">
            <code className="text-[1.05rem] font-semibold text-accent">.ots</code>
          </div>
          <p className="mt-5 text-ink">contrato-locacion.ots</p>
          <code className="block text-muted">1,3 KB</code>
          <p className="mt-4 text-muted">Verificable con cualquier cliente de OpenTimestamps.</p>
        </Fragment>
      ),
    },
    {
      id: "api",
      title: "Tu app, con una secret key",
      body: "El API es el mismo que usa esta web. Creás paquetes desde tu backend con una secret key; verificar por hash es público y no pide cuenta.",
      fragment: (
        <Fragment label="Pedido al API con una secret key, de ejemplo" className="w-full sm:w-[400px]">
          <div className="flex items-center justify-between gap-3 bg-surface-2 px-5 py-3 text-[0.8125rem]">
            <code className="text-ink">sk_live_••••••••4f2a</code>
            <span className="text-muted">ejemplo</span>
          </div>
          <div className="code-block text-[0.75rem]" dangerouslySetInnerHTML={{ __html: apiHtml }} />
        </Fragment>
      ),
    },
  ];

  return (
    <section id="que-queda" aria-labelledby="queda-title" className="frame-x pt-[var(--gap)]">
      <div className="lg:pl-[33.333%]">
        <h2 id="queda-title" className="head max-w-[12ch] text-[length:var(--step-head)]" data-reveal>
          Lo que queda de tu archivo
        </h2>
      </div>
      <ul className="mt-20 space-y-[clamp(64px,6vw,96px)] lg:pl-[33.333%]">
        {rows.map((row, i) => (
          <li key={row.title} id={row.id} className="flex scroll-mt-24 flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
            <div className="max-w-[34ch]" data-reveal>
              <h3 className="head text-[clamp(2rem,1.2rem+2.2vw,3.25rem)]">{row.title}</h3>
              <p className="mt-4">{row.body}</p>
            </div>
            <div
              data-reveal
              style={{ "--i": 1 } as React.CSSProperties}
              className={i % 2 === 0 ? "sm:self-start" : "sm:self-start sm:mt-10"}
            >
              {row.fragment}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
