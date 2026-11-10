"use client";

import { useId, useState } from "react";
import { Check, Loader2 } from "lucide-react";

/**
 * Handler simulado: todavía no hay backend para la lista de espera.
 * TODO: reemplazar por un POST real (por ejemplo, /waitlist en el API de Hashly) antes de publicar.
 * Hoy el email no se guarda en ningún lado.
 */
async function joinWaitlist(email: string, interest: "bitcoin" | "contrato"): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 700));
  if (process.env.NODE_ENV !== "production") console.info("[lista de espera simulada]", email, interest);
}

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function Pricing() {
  const [email, setEmail] = useState("");
  const [interest, setInterest] = useState<"bitcoin" | "contrato">("bitcoin");
  const [state, setState] = useState<"idle" | "sending" | "done" | "invalid">("idle");
  const id = useId();

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!EMAIL.test(email.trim())) {
      setState("invalid");
      return;
    }
    setState("sending");
    await joinWaitlist(email.trim(), interest);
    setState("done");
  }

  return (
    <section id="precio" aria-labelledby="precio-title" className="mt-[var(--gap)] flex min-h-[86svh] flex-col justify-center bg-surface py-24">
      <div className="frame-x">
        <h2 id="precio-title" className="display text-[length:var(--step-display)] leading-[0.95]" data-reveal>
          <span className="block">Sellar en Bitcoin</span>
          <span className="block">
            cuesta{" "}
            <span className="inline-block bg-accent px-[0.15em] leading-[1] text-accent-ink">0 USD</span>
          </span>
        </h2>

        <div className="mt-16 grid grid-cols-1 gap-10 lg:grid-cols-12 lg:items-end">
          <div className="lg:col-span-6" data-reveal style={{ "--i": 1 } as React.CSSProperties}>
            <p className="text-[length:var(--step-lead)] leading-snug">
              Incluye la prueba .ots y la verificación pública por hash. La confirmación en Bitcoin tarda unas horas.
            </p>
            <p className="mt-5 text-muted">
              ¿Lo necesitás en segundos? La vía por contrato en una L2 va a cobrarse pagando con tu wallet y te deja un certificado
              NFT. Todavía no está disponible.
            </p>
          </div>

          <div className="lg:col-span-5 lg:col-start-8" data-reveal style={{ "--i": 2 } as React.CSSProperties}>
            {state === "done" ? (
              <p role="status" className="flex items-start gap-3 text-[length:var(--step-lead)] leading-snug">
                <Check className="mt-1 shrink-0 text-ok" aria-hidden />
                Listo. Te escribimos a {email.trim()} cuando abra {interest === "bitcoin" ? "Hashly" : "la vía por contrato"}.
              </p>
            ) : (
              <form onSubmit={submit} noValidate>
                <p className="text-muted">Hashly está en desarrollo. Dejanos tu email y te avisamos cuando abra.</p>
                <fieldset className="mt-5 flex flex-wrap gap-2">
                  <legend className="sr-only">Qué vía te interesa</legend>
                  {(
                    [
                      ["bitcoin", "Bitcoin, gratis"],
                      ["contrato", "Contrato, con wallet"],
                    ] as const
                  ).map(([value, label]) => (
                    <label
                      key={value}
                      className={`cursor-pointer px-4 py-2.5 text-[0.95rem] transition-colors has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent ${
                        interest === value ? "bg-ink text-bg" : "bg-surface-2 text-ink hover:bg-[#1d2742]"
                      }`}
                    >
                      <input type="radio" name="interest" value={value} checked={interest === value} onChange={() => setInterest(value)} className="sr-only" />
                      {label}
                    </label>
                  ))}
                </fieldset>
                <label htmlFor={id} className="sr-only">
                  Tu email
                </label>
                <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                  <input
                    id={id}
                    type="email"
                    inputMode="email"
                    autoComplete="email"
                    placeholder="tu@email.com"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (state === "invalid") setState("idle");
                    }}
                    aria-invalid={state === "invalid"}
                    aria-describedby={`${id}-error`}
                    className="h-[3.25rem] w-full min-w-0 bg-bg px-4 text-ink placeholder:text-muted sm:flex-1"
                  />
                  <button type="submit" className="btn btn-accent" disabled={state === "sending"}>
                    {state === "sending" && <Loader2 size={16} className="animate-spin" aria-hidden />}
                    {state === "sending" ? "Anotando…" : "Avisame"}
                  </button>
                </div>
                <p id={`${id}-error`} aria-live="polite" className="mt-2 min-h-5 text-[length:var(--step-small)] text-accent">
                  {state === "invalid" ? "Revisá el email: le falta algo para ser una dirección válida." : ""}
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
