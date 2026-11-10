"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api, setToken } from "@/lib/api";
import { ErrorNote, Field, Shell, inputClass } from "@/components/app/Shell";

export default function Entrar() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") await api.register(email, password);
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      router.push("/panel");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Algo salió mal");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Shell>
      <h1 className="head text-[length:var(--step-head)]">{mode === "login" ? "Entrar" : "Crear cuenta"}</h1>
      <p className="mt-4 text-muted">
        {mode === "login"
          ? "Accedé a tus paquetes sellados y a tus API keys."
          : "Gratis. Sellá tus archivos en Bitcoin sin que salgan de tu equipo."}
      </p>

      <form onSubmit={submit} className="mt-10 grid gap-5">
        <Field label="Email">
          <input
            className={inputClass}
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Contraseña (mínimo 8 caracteres)">
          <input
            className={inputClass}
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            minLength={8}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <ErrorNote message={error} />
        <button className="btn btn-accent" disabled={busy}>
          {busy ? "Un momento…" : mode === "login" ? "Entrar" : "Crear cuenta"}
        </button>
      </form>

      <p className="mt-8 text-[length:var(--step-small)] text-muted">
        {mode === "login" ? "¿No tenés cuenta? " : "¿Ya tenés cuenta? "}
        <button className="link text-ink" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Crear una" : "Entrar"}
        </button>
      </p>
    </Shell>
  );
}
