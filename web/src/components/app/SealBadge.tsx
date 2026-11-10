import type { Seal } from "@/lib/api";

const LABELS: Record<NonNullable<Seal>["status"], { text: string; hint: string }> = {
  creating: { text: "Enviando", hint: "Mandando la huella a los calendar servers" },
  pending: { text: "Esperando Bitcoin", hint: "Suele confirmarse en unas horas" },
  confirmed: { text: "Sellado en Bitcoin", hint: "Confirmado" },
  failed: { text: "Falló", hint: "No se pudo confirmar a tiempo" },
};

export function SealBadge({ seal }: { seal: Seal }) {
  if (!seal) return <span className="text-muted">Sin sello</span>;

  const { text, hint } = LABELS[seal.status];
  const tone =
    seal.status === "confirmed" ? "text-ok" : seal.status === "failed" ? "text-muted" : "text-accent";

  return (
    <span className={`inline-flex items-center gap-2 ${tone}`} title={hint}>
      <span aria-hidden className="inline-block h-2 w-2 rounded-full bg-current" />
      <span>
        {text}
        {seal.bitcoin_block_height ? ` · bloque ${seal.bitcoin_block_height.toLocaleString("es-AR")}` : ""}
      </span>
    </span>
  );
}
