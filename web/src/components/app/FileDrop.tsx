"use client";

import { useRef, useState } from "react";

type Props = { files: File[]; onChange: (files: File[]) => void };

/** Zona para soltar archivos. Los archivos solo se hashean en el servidor y se descartan. */
export function FileDrop({ files, onChange }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  function add(list: FileList | null) {
    if (!list) return;
    const names = new Set(files.map((f) => f.name.toLowerCase()));
    const next = [...files];
    for (const f of Array.from(list)) {
      if (!names.has(f.name.toLowerCase())) {
        names.add(f.name.toLowerCase());
        next.push(f);
      }
    }
    onChange(next);
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          add(e.dataTransfer.files);
        }}
        className={`grid min-h-32 place-items-center rounded-[4px] border border-dashed px-4 py-6 text-center transition-colors ${
          over ? "border-accent bg-surface-2" : "border-muted/50 bg-surface"
        }`}
      >
        <div className="grid gap-3">
          <p className="text-muted">Soltá tus archivos acá</p>
          <button type="button" className="btn btn-quiet !min-h-11" onClick={() => input.current?.click()}>
            Elegir archivos
          </button>
        </div>
        <input ref={input} type="file" multiple className="sr-only" onChange={(e) => add(e.target.files)} />
      </div>

      {files.length > 0 && (
        <ul className="mt-3 grid gap-1 text-[length:var(--step-small)]">
          {files.map((f) => (
            <li key={f.name} className="flex items-center justify-between gap-4 rounded-[4px] bg-surface px-3 py-2">
              <span className="truncate">{f.name}</span>
              <button
                type="button"
                className="shrink-0 text-muted hover:text-accent"
                onClick={() => onChange(files.filter((x) => x !== f))}
                aria-label={`Quitar ${f.name}`}
              >
                Quitar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
