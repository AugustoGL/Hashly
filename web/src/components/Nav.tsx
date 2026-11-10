const links = [
  { href: "#como-funciona", label: "Cómo funciona" },
  { href: "#probalo", label: "Probalo" },
  { href: "#precio", label: "Precio" },
];

/** Barra simple: marca, tres enlaces y una acción. Vive sobre el hero y se va con el scroll. */
export function Nav() {
  return (
    <header className="frame-x absolute inset-x-0 top-0 z-30 flex h-20 items-center justify-between gap-6 text-[length:var(--step-small)]">
      <a href="#" className="display text-[length:var(--step-lead)] leading-none tracking-normal" aria-label="Hashly, inicio">
        Hashly
      </a>
      <nav aria-label="Secciones" className="hidden md:block">
        <ul className="flex gap-8">
          {links.map((l) => (
            <li key={l.href}>
              <a href={l.href} className="transition-colors hover:text-accent">
                {l.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <a href="#precio" className="btn btn-quiet !min-h-11 !px-4 !py-2">
        Avisame
      </a>
    </header>
  );
}
