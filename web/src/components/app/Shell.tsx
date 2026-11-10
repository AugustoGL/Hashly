import Link from "next/link";
import type { ReactNode } from "react";

/** Marco común de las pantallas de la app: marca, navegación y un ancho cómodo. */
export function Shell({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <>
      <header className="frame-x flex h-20 items-center justify-between gap-6 text-[length:var(--step-small)]">
        <Link href="/" className="display text-[length:var(--step-lead)] leading-none tracking-normal" aria-label="Hashly, inicio">
          Hashly
        </Link>
        <nav aria-label="Principal">
          <ul className="flex items-center gap-6">
            <li>
              <Link href="/verificar" className="transition-colors hover:text-accent">
                Verificar
              </Link>
            </li>
            <li>
              <Link href="/panel" className="transition-colors hover:text-accent">
                Mi panel
              </Link>
            </li>
          </ul>
        </nav>
      </header>
      <main id="contenido" className={`frame-x mx-auto pb-24 pt-8 ${wide ? "max-w-5xl" : "max-w-xl"}`}>
        {children}
      </main>
    </>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="grid gap-2 text-[length:var(--step-small)]">
      <span className="text-muted">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "min-h-12 w-full rounded-[4px] border border-surface-2 bg-surface px-4 text-ink placeholder:text-muted focus:border-accent";

export function ErrorNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded-[4px] border border-accent/40 bg-surface px-4 py-3 text-[length:var(--step-small)]">
      {message}
    </p>
  );
}
