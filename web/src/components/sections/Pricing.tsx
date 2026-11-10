"use client";

import { useId, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { api } from "@/lib/api";


const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function Pricing() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "invalid" | "error">("idle");
  const id = useId();

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!EMAIL.test(email.trim())) {
      setState("invalid");
      return;
    }
    setState("sending");
    try {
      await api.joinWaitlist(email.trim(), "contrato");
      setState("done");
    } catch {
      setState("error");
    }
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
                Listo. Te escribimos a {email.trim()} cuando abra la vía por contrato.
              </p>
            ) : (
              <form onSubmit={submit} noValidate>
                <p className="text-muted">
                  La vía gratis ya está abierta:{" "}
                  <a href="/entrar" className="link text-ink">
                    creá tu cuenta
                  </a>
                  . Para la vía por contrato, dejanos tu email y te avisamos cuando abra.
                </p>
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
                  {state === "invalid"
                    ? "Revisá el email: le falta algo para ser una dirección válida."
                    : state === "error"
                      ? "No pudimos anotarte. Probá de nuevo en un rato."
                      : ""}
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
