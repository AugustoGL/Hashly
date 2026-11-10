"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  API_URL,
  ApiError,
  api,
  setToken,
  getToken,
  type ApiKeyRow,
  type FileProof,
  type PackageDetail,
  type PackageSummary,
} from "@/lib/api";
import { FileDrop } from "@/components/app/FileDrop";
import { SealBadge } from "@/components/app/SealBadge";
import { CopyButton } from "@/components/CopyButton";
import { ErrorNote, Field, Shell, inputClass } from "@/components/app/Shell";

const fmt = (iso: string) => new Date(iso + "Z").toLocaleString("es-AR");

export default function Panel() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [packages, setPackages] = useState<PackageSummary[]>([]);
  const [keys, setKeys] = useState<ApiKeyRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    setToken(null);
    router.push("/entrar");
  }, [router]);

  const load = useCallback(async () => {
    try {
      const [pk, ks] = await Promise.all([api.packages(), api.keys()]);
      setPackages(pk.slice().reverse());
      setKeys(ks);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) return logout();
      setError(err instanceof Error ? err.message : "Algo salió mal");
    }
  }, [logout]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/entrar");
      return;
    }
    void (async () => {
      try {
        setEmail((await api.me()).email);
      } catch {
        logout();
        return;
      }
      await load();
    })();
  }, [router, load, logout]);

  // Mientras haya sellos en curso, refrescamos cada 30 s
  const inFlight = packages.some((p) => p.seal && (p.seal.status === "creating" || p.seal.status === "pending"));
  useEffect(() => {
    if (!inFlight) return;
    const t = window.setInterval(load, 30_000);
    return () => window.clearInterval(t);
  }, [inFlight, load]);

  if (!email) return <Shell wide>{error ? <ErrorNote message={error} /> : <p className="text-muted">Cargando…</p>}</Shell>;

  return (
    <Shell wide>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="head text-[length:var(--step-head)]">Mi panel</h1>
          <p className="mt-3 text-muted">{email}</p>
        </div>
        <button className="btn btn-quiet !min-h-11" onClick={logout}>
          Salir
        </button>
      </div>
      <ErrorNote message={error} />

      <NewPackage onCreated={load} />
      <PackageList packages={packages} />
      <Keys keys={keys} onChange={load} />
    </Shell>
  );
}

/* ---------------- Nuevo paquete ---------------- */

function NewPackage({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.createPackage(name, files);
      setName("");
      setFiles([]);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo salió mal");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-14" aria-labelledby="nuevo">
      <h2 id="nuevo" className="text-[length:var(--step-lead)] font-medium">
        Sellar archivos
      </h2>
      <p className="mt-2 max-w-prose text-muted">
        Se calcula la huella de cada archivo, se arma el árbol de Merkle y se sella la raíz en Bitcoin. Los archivos no
        se guardan.
      </p>
      <form onSubmit={submit} className="mt-6 grid max-w-xl gap-5">
        <Field label="Nombre del paquete">
          <input className={inputClass} required maxLength={255} value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <FileDrop files={files} onChange={setFiles} />
        <ErrorNote message={error} />
        <button className="btn btn-accent" disabled={busy || files.length === 0 || !name.trim()}>
          {busy ? "Sellando…" : "Sellar en Bitcoin"}
        </button>
        <p className="text-[length:var(--step-small)] text-muted">
          La vía por contrato (certificado NFT) llega próximamente.
        </p>
      </form>
    </section>
  );
}

/* ---------------- Mis paquetes ---------------- */

function PackageList({ packages }: { packages: PackageSummary[] }) {
  return (
    <section className="mt-16" aria-labelledby="paquetes">
      <h2 id="paquetes" className="text-[length:var(--step-lead)] font-medium">
        Mis paquetes
      </h2>
      {packages.length === 0 ? (
        <p className="mt-4 text-muted">Todavía no sellaste nada.</p>
      ) : (
        <ul className="mt-6 grid gap-3">
          {packages.map((p) => (
            <PackageRow key={p.id} pkg={p} />
          ))}
        </ul>
      )}
    </section>
  );
}

function PackageRow({ pkg }: { pkg: PackageSummary }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<PackageDetail | null>(null);
  const [proof, setProof] = useState<FileProof | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function toggle() {
    setOpen(!open);
    if (!open && !detail) {
      try {
        setDetail(await api.package(pkg.id));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Algo salió mal");
      }
    }
  }

  async function showProof(filename: string) {
    try {
      setProof(await api.fileProof(pkg.id, filename));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo salió mal");
    }
  }

  async function downloadOts() {
    try {
      const res = await fetch(api.otsProofUrl(pkg.id));
      if (!res.ok) throw new Error("Todavía no hay prueba disponible");
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = `hashly-${pkg.id}.ots`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo salió mal");
    }
  }

  return (
    <li className="rounded-[4px] bg-surface">
      <button
        className="flex w-full flex-wrap items-center justify-between gap-3 px-4 py-4 text-left"
        onClick={toggle}
        aria-expanded={open}
      >
        <span>
          <span className="block font-medium">{pkg.name}</span>
          <span className="text-[length:var(--step-small)] text-muted">{fmt(pkg.created_at)}</span>
        </span>
        <span className="text-[length:var(--step-small)]">
          <SealBadge seal={pkg.seal} />
        </span>
      </button>

      {open && (
        <div className="grid gap-4 border-t border-surface-2 px-4 py-4 text-[length:var(--step-small)]">
          <ErrorNote message={error} />
          <div className="flex items-center gap-3">
            <span className="text-muted">Raíz</span>
            <code className="truncate">{pkg.merkle_root}</code>
            <CopyButton value={pkg.merkle_root} label="Copiar raíz" variant="icon" />
          </div>

          <div>
            <button className="btn btn-quiet !min-h-11" onClick={downloadOts} disabled={!pkg.seal || pkg.seal.status === "creating"}>
              Descargar prueba .ots
            </button>
          </div>

          {detail && (
            <ul className="grid gap-2">
              {detail.manifest.map((m) => (
                <li key={m.hash} className="flex flex-wrap items-center justify-between gap-2 rounded-[4px] bg-bg px-3 py-2">
                  <span className="truncate">{m.filename}</span>
                  <span className="flex items-center gap-3">
                    <code className="text-muted">{m.hash.slice(0, 12)}…</code>
                    <button className="link" onClick={() => showProof(m.filename)}>
                      Prueba de Merkle
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}

          {proof && (
            <div className="grid gap-2">
              <p className="text-muted">Prueba de «{proof.filename}»</p>
              <pre className="overflow-x-auto rounded-[4px] bg-bg p-3">{JSON.stringify(proof, null, 2)}</pre>
              <div>
                <CopyButton value={JSON.stringify(proof, null, 2)} label="Copiar prueba" />
              </div>
            </div>
          )}
        </div>
      )}
    </li>
  );
}

/* ---------------- API keys ---------------- */

function Keys({ keys, onChange }: { keys: ApiKeyRow[]; onChange: () => void }) {
  const [name, setName] = useState("");
  const [fresh, setFresh] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function create(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await api.createKey(name);
      setFresh(created.key);
      setName("");
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo salió mal");
    }
  }

  async function revoke(id: number) {
    try {
      await api.revokeKey(id);
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo salió mal");
    }
  }

  return (
    <section className="mt-16" aria-labelledby="keys">
      <h2 id="keys" className="text-[length:var(--step-lead)] font-medium">
        API keys
      </h2>
      <p className="mt-2 max-w-prose text-muted">
        Usalas desde tu propia app: <code>Authorization: Bearer hshl_live_…</code>. Mirá la{" "}
        <a className="link" href={`${API_URL}/docs`}>
          documentación del API
        </a>
        .
      </p>

      <form onSubmit={create} className="mt-6 flex max-w-xl flex-wrap items-end gap-3">
        <div className="min-w-48 flex-1">
          <Field label="Nombre de la key">
            <input className={inputClass} required maxLength={100} value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
        </div>
        <button className="btn btn-quiet" disabled={!name.trim()}>
          Crear key
        </button>
      </form>

      <div className="mt-4 grid max-w-xl gap-3">
        <ErrorNote message={error} />
        {fresh && (
          <div className="rounded-[4px] border border-accent/40 bg-surface p-4" role="status">
            <p className="font-medium">Copiá tu key ahora: no se vuelve a mostrar.</p>
            <p className="mt-3 flex items-center gap-3">
              <code className="truncate">{fresh}</code>
              <CopyButton value={fresh} label="Copiar key" variant="icon" />
            </p>
          </div>
        )}
      </div>

      {keys.length > 0 && (
        <ul className="mt-6 grid max-w-xl gap-2">
          {keys.map((k) => (
            <li key={k.id} className="flex items-center justify-between gap-3 rounded-[4px] bg-surface px-4 py-3">
              <span>
                <span className="block">{k.name}</span>
                <span className="text-[length:var(--step-small)] text-muted">
                  <code>{k.prefix}…</code> · {k.revoked ? "revocada" : k.last_used_at ? `usada ${fmt(k.last_used_at)}` : "sin usar"}
                </span>
              </span>
              {!k.revoked && (
                <button className="link text-[length:var(--step-small)]" onClick={() => revoke(k.id)}>
                  Revocar
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
