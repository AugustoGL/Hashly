"use client";

import { useState, type FormEvent } from "react";
import { api, type SearchResult } from "@/lib/api";
import { FileDrop } from "@/components/app/FileDrop";
import { SealBadge } from "@/components/app/SealBadge";
import { CopyButton } from "@/components/CopyButton";
import { ErrorNote, Field, Shell, inputClass } from "@/components/app/Shell";

export default function Verificar() {
  const [root, setRoot] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(fn: () => Promise<SearchResult>) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setResult(await fn());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo salió mal");
    } finally {
      setBusy(false);
    }
  }

  const byRoot = (e: FormEvent) => {
    e.preventDefault();
    run(() => api.searchRoot(root.trim()));
  };

  return (
    <Shell>
      <h1 className="head text-[length:var(--step-head)]">Verificar</h1>
      <p className="mt-4 text-muted">
        Sin cuenta. Soltá tus archivos o pegá la raíz de Merkle: si fueron sellados, vas a ver desde cuándo. Nunca se
        muestra de quién son ni cómo se llaman.
      </p>

      <section className="mt-10 grid gap-4" aria-labelledby="por-archivos">
        <h2 id="por-archivos" className="text-[length:var(--step-lead)] font-medium">
          Por archivos
        </h2>
        <FileDrop files={files} onChange={setFiles} />
        <button
          className="btn btn-accent"
          disabled={busy || files.length === 0}
          onClick={() => run(() => api.searchFiles(files))}
        >
          Verificar archivos
        </button>
      </section>

      <form onSubmit={byRoot} className="mt-12 grid gap-4" aria-labelledby="por-raiz">
        <h2 id="por-raiz" className="text-[length:var(--step-lead)] font-medium">
          Por raíz de Merkle
        </h2>
        <Field label="64 caracteres hexadecimales">
          <input
            className={`${inputClass} font-mono`}
            value={root}
            onChange={(e) => setRoot(e.target.value)}
            spellCheck={false}
            placeholder="9f86d0…"
          />
        </Field>
        <button className="btn btn-quiet" disabled={busy || !root.trim()}>
          Buscar
        </button>
      </form>

      <div className="mt-10 grid gap-4" aria-live="polite">
        <ErrorNote message={error} />
        {result && !result.found && (
          <p className="rounded-[4px] bg-surface px-4 py-4">
            <strong>No se encontró.</strong> Esa combinación de archivos no está sellada, o alguno cambió aunque sea un
            byte.
          </p>
        )}
        {result?.found && (
          <div className="rounded-[4px] bg-surface px-4 py-4">
            <p className="text-ok">
              <strong>Coincide.</strong> Estos archivos existían sin cambios desde la fecha del sello.
            </p>
            <p className="mt-3 flex items-center gap-3 text-[length:var(--step-small)] text-muted">
              <code className="truncate">{result.merkle_root}</code>
              <CopyButton value={result.merkle_root} label="Copiar raíz" variant="icon" />
            </p>
            <ul className="mt-4 grid gap-3">
              {result.packages.map((p) => (
                <li key={p.id} className="grid gap-1 border-t border-surface-2 pt-3">
                  <span>Sellado el {new Date(p.created_at + "Z").toLocaleString("es-AR")}</span>
                  <SealBadge seal={p.seal} />
                  {p.seal && (
                    <a className="link w-fit text-[length:var(--step-small)]" href={api.otsProofUrl(p.id)}>
                      Descargar prueba .ots
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Shell>
  );
}
