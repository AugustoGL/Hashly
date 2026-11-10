const faq = [
  {
    q: "¿Qué pasa si Hashly desaparece?",
    a: "Tu prueba sigue valiendo. El archivo .ots se verifica contra Bitcoin con cualquier cliente de OpenTimestamps, sin pasar por nosotros.",
  },
  {
    q: "¿Hashly ve mis archivos?",
    a: "Los procesa en memoria para calcular su hash y los descarta en el momento. La demo de esta página ni siquiera los envía: calcula todo en tu navegador.",
  },
  {
    q: "¿Qué formatos acepta?",
    a: "Texto (TXT, MD, JSON, código), imágenes (JPG, PNG, WebP, BMP, TIFF) y PDF. Antes de hashear, cada formato se normaliza y se le suma el nombre del archivo.",
  },
  {
    q: "¿Cuánto tarda el sello?",
    a: "En Bitcoin, unas horas: lo que tarda la raíz en entrar en un bloque. La vía por contrato, cuando esté disponible, va a tardar segundos.",
  },
  {
    q: "¿Necesito una wallet?",
    a: "Para la vía de Bitcoin, no. Para la vía por contrato sí: vas a pagar el sello conectando tu wallet y el certificado NFT queda a tu nombre.",
  },
  {
    q: "¿Cómo verifica alguien mi archivo?",
    a: "Vuelve a calcular el hash, recorre el camino hasta la raíz y la busca por merkle_root. Esa búsqueda es pública y no pide cuenta.",
  },
];

export function Faq() {
  return (
    <section id="preguntas" aria-labelledby="faq-title" className="frame-x pt-[var(--gap)]">
      <dl className="grid grid-cols-1 gap-y-12 lg:grid-cols-12 lg:gap-y-14">
        <div className="lg:col-span-6">
          <h2 id="faq-title" className="head text-[clamp(2rem,1.2rem+2.2vw,3.25rem)] text-muted" data-reveal>
            Preguntas
          </h2>
        </div>
        <div className="hidden lg:col-span-6 lg:block" />
        {faq.map((item) => (
          <div key={item.q} className="contents">
            <dt className="head text-[clamp(2rem,1.2rem+2.2vw,3.25rem)] lg:col-span-6" data-reveal>
              {item.q}
            </dt>
            <dd className="-mt-10 max-w-[42ch] lg:col-span-5 lg:col-start-8 lg:mt-0" data-reveal style={{ "--i": 1 } as React.CSSProperties}>
              {item.a}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function Cta() {
  return (
    <section aria-labelledby="cta-title" className="frame-x mt-[var(--gap)] flex min-h-[56svh] flex-col justify-between py-8 text-center md:min-h-[82svh]">
      <h2 id="cta-title" className="display text-[length:var(--step-display)]" data-reveal>
        ¿Lo probás
      </h2>
      <div className="flex flex-col items-center gap-4 py-16" data-reveal style={{ "--i": 1 } as React.CSSProperties}>
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:gap-8">
          <a href="#probalo" className="btn btn-accent w-[72vw] sm:w-52">
            Probar la demo
          </a>
          <span className="text-muted">o</span>
          <a href="/entrar" className="btn btn-quiet w-[72vw] sm:w-52">
            Crear cuenta
          </a>
        </div>
        <p className="text-muted">La demo corre en tu navegador. Con una cuenta sellás de verdad y obtenés tu API key.</p>
      </div>
      <p className="display text-[length:var(--step-display)]" data-reveal style={{ "--i": 2 } as React.CSSProperties}>
        o lo integrás?
      </p>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="frame-x flex min-h-[90svh] flex-col bg-accent py-10 text-accent-ink">
      <div className="flex flex-wrap items-start justify-between gap-6 text-[0.95rem]">
        <div className="max-w-[28rem]">
          <p className="display text-[1.75rem] leading-none">Hashly</p>
          <p className="mt-3">Prueba de existencia de archivos, sellada en Bitcoin. Los archivos nunca se guardan.</p>
        </div>
        <a href="#contenido" className="link">
          Volver arriba
        </a>
      </div>
      <div className="mt-auto pt-24">
        <p className="text-[0.95rem]">Código abierto, licencia MIT</p>
        <a
          href="https://github.com/AugustoGL/Hashly"
          target="_blank"
          rel="noreferrer"
          className="display mt-2 block break-words text-[length:var(--step-display)] leading-[0.9] transition-opacity hover:opacity-80"
        >
          Descargalo en GitHub
          <span className="sr-only"> (se abre en otra pestaña)</span>
        </a>
      </div>
      <div className="mt-12 flex flex-col gap-2 text-[0.875rem] sm:flex-row sm:justify-between">
        <p className="flex gap-5">
          <a className="link" href="https://opentimestamps.org" target="_blank" rel="noreferrer">
            OpenTimestamps<span className="sr-only"> (se abre en otra pestaña)</span>
          </a>
          <a className="link" href="https://www.rfc-editor.org/rfc/rfc6962#section-2.1" target="_blank" rel="noreferrer">
            RFC 6962<span className="sr-only"> (se abre en otra pestaña)</span>
          </a>
        </p>
        <p>Escena 3D en WebGPU, hecha con Three.js</p>
        <p>2026</p>
      </div>
    </footer>
  );
}
