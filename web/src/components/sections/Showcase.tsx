"use client";

import { useEffect, useId, useRef, useState } from "react";
import clsx from "clsx";
import { FileUp, X } from "lucide-react";
import { buildTree, leafHash, sha256Hex, sortByName, type MerkleNode } from "@/lib/merkle";
import { CopyButton } from "../CopyButton";
import { MerkleTreeView } from "../demo/MerkleTreeView";

const examples = ["Contrato firmado el 3 de marzo", "Contrato firmado el 4 de marzo", "contrato firmado el 3 de marzo"];
const MAX_FILES = 16;

type Hashed = { name: string; hash: string };

/**
 * Lo único vivo de la página: el titular es un campo de texto y debajo aparece su
 * SHA-256 en cada tecla. Cambiar una letra cambia casi toda la huella.
 * Todo corre con Web Crypto en el navegador.
 */
export function Showcase() {
  const [text, setText] = useState(examples[0]);
  const [hash, setHash] = useState<string | null>(null);
  const [previous, setPrevious] = useState<string | null>(null);
  const [files, setFiles] = useState<Hashed[]>([]);
  const [tree, setTree] = useState<MerkleNode | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputId = useId();
  const fileId = useId();
  const last = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    sha256Hex(new TextEncoder().encode(text)).then((h) => {
      if (cancelled) return;
      setPrevious(last.current);
      last.current = h;
      setHash(h);
    });
    return () => {
      cancelled = true;
    };
  }, [text]);

  const changed = hash && previous && previous !== hash ? [...hash].filter((c, i) => c !== previous[i]).length : null;

  async function addFiles(list: File[]) {
    setFileError(null);
    const names = new Set(files.map((f) => f.name.toLowerCase()));
    const next = [...files];
    for (const file of list) {
      if (names.has(file.name.toLowerCase())) {
        setFileError(`Ya hay un archivo llamado "${file.name}". Renombrá uno: el servicio tampoco acepta nombres repetidos.`);
        continue;
      }
      if (next.length >= MAX_FILES) {
        setFileError(`La demo dibuja hasta ${MAX_FILES} archivos.`);
        break;
      }
      names.add(file.name.toLowerCase());
      next.push({ name: file.name, hash: await leafHash(await file.arrayBuffer()) });
    }
    const sorted = sortByName(next);
    setFiles(sorted);
    setTree(sorted.length ? await buildTree(sorted.map((f) => ({ hash: f.hash, fileName: f.name }))) : null);
  }

  async function removeFile(name: string) {
    const next = files.filter((f) => f.name !== name);
    setFiles(next);
    setTree(next.length ? await buildTree(next.map((f) => ({ hash: f.hash, fileName: f.name }))) : null);
  }

  return (
    <section id="probalo" aria-labelledby="probalo-title" className="frame-x relative pt-[var(--gap)]">
      <h2 id="probalo-title" className="head max-w-[16ch] text-[length:var(--step-head)]" data-reveal>
        Escribí algo y mirá su huella
      </h2>

      <label htmlFor={inputId} className="sr-only">
        Texto para calcular su SHA-256
      </label>
      <div className="relative mt-10" data-ui data-reveal style={{ "--i": 1 } as React.CSSProperties}>
        <input
          id={inputId}
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
          autoComplete="off"
          className="w-full border-0 bg-transparent p-0 font-[family-name:var(--font-display)] text-[length:var(--step-display)] leading-[1.05] tracking-[-0.01em] text-ink caret-accent outline-none focus-visible:outline-none"
        />
        <span aria-hidden className="pointer-events-none absolute -bottom-2 left-0 h-[3px] w-full bg-surface-2" />
      </div>

      <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Respuesta: la huella del texto */}
        <div data-ui data-reveal style={{ "--i": 2 } as React.CSSProperties} className="rounded-[6px] bg-surface p-6 lg:col-span-6">
          <div className="flex items-center justify-between gap-4">
            <p className="text-[length:var(--step-small)] text-muted">SHA-256 de este texto</p>
            {hash && <CopyButton value={hash} label="Copiar el SHA-256" variant="icon" />}
          </div>
          <code className="mt-3 block break-all text-[length:var(--step-lead)] leading-relaxed" aria-live="polite">
            {hash
              ? [...hash].map((c, i) => (
                  <span key={i} className={clsx(previous && previous[i] !== c && "text-accent")}>
                    {c}
                  </span>
                ))
              : "calculando…"}
          </code>
          <p className="mt-4 text-[length:var(--step-small)] text-muted">
            {changed !== null
              ? `Cambiaron ${changed} de 64 caracteres. Por eso nadie puede alterar un archivo sin que se note.`
              : "Cambiá una sola letra y mirá cuántos caracteres cambian."}
          </p>
          <p className="mt-2 text-[length:var(--step-small)] text-muted">
            Comprobalo en tu terminal: <code className="break-all text-ink">echo -n &apos;{text}&apos; | sha256sum</code>
          </p>
        </div>

        {/* Archivos: el árbol completo */}
        <div
          data-ui
          data-reveal
          style={{ "--i": 3 } as React.CSSProperties}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            addFiles([...e.dataTransfer.files]);
          }}
          className={clsx(
            "flex flex-col rounded-[6px] p-6 transition-colors lg:col-span-6",
            dragging ? "bg-surface-2" : "bg-surface",
          )}
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-[length:var(--step-small)] text-muted">
              {files.length ? `merkle_root de ${files.length} ${files.length === 1 ? "archivo" : "archivos"}` : "¿Tenés archivos? Soltalos acá"}
            </p>
            <label htmlFor={fileId} className="btn btn-quiet !min-h-10 cursor-pointer !px-4 !py-2 text-[0.95rem] has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent">
              <FileUp size={16} aria-hidden />
              Elegir archivos
            </label>
            <input
              id={fileId}
              type="file"
              multiple
              className="sr-only"
              onChange={(e) => {
                addFiles([...(e.target.files ?? [])]);
                e.target.value = "";
              }}
            />
          </div>

          {tree ? (
            <>
              <div className="mt-3 flex items-start justify-between gap-3">
                <code className="block break-all leading-relaxed">{tree.hash}</code>
                <CopyButton value={tree.hash} label="Copiar el merkle_root" variant="icon" />
              </div>
              <div className="-mx-2 mt-4 overflow-x-auto" data-lenis-prevent>
                <MerkleTreeView root={tree} selectedId={tree.id} onSelect={() => {}} reduced={false} />
              </div>
              <ul className="mt-4 flex flex-wrap gap-2">
                {files.map((f) => (
                  <li key={f.name} className="flex items-center gap-1 rounded-[4px] bg-surface-2 py-1 pl-3 pr-1 text-[length:var(--step-small)]">
                    {f.name}
                    <button type="button" aria-label={`Quitar ${f.name}`} onClick={() => removeFile(f.name)} className="grid h-7 w-7 place-items-center hover:text-accent">
                      <X size={14} aria-hidden />
                    </button>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="mt-auto pt-10 text-muted">
              Calculamos el hash de cada uno y armamos el árbol de Merkle con las mismas reglas que usa Hashly. No sube nada y no
              sella nada.
            </p>
          )}
          <p role="status" className="mt-3 min-h-5 text-[length:var(--step-small)] text-accent">
            {fileError}
          </p>
        </div>
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-3" data-reveal style={{ "--i": 4 } as React.CSSProperties}>
        <span className="text-[length:var(--step-small)] text-muted">Probá con</span>
        {examples.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => setText(ex)}
            className={clsx("btn !min-h-11 !px-4 !py-2 text-[0.95rem]", text === ex ? "btn-accent" : "btn-quiet")}
          >
            {ex}
          </button>
        ))}
      </div>
      <p className="mt-6 max-w-[60ch] text-[length:var(--step-small)] text-muted">
        Todo esto pasa en tu navegador. Para los archivos, el servicio además agrega el nombre y normaliza el contenido antes de
        hashear, así que su raíz no va a coincidir con la de esta demo.
      </p>
    </section>
  );
}
