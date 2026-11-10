"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check, Copy } from "lucide-react";
import clsx from "clsx";

type Props = {
  value: string;
  label: string;
  className?: string;
  variant?: "icon" | "pill";
};

export function CopyButton({ value, label, className, variant = "pill" }: Props) {
  const [state, setState] = useState<"idle" | "copied" | "error">("idle");
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setState("copied");
    } catch {
      setState("error");
    }
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setState("idle"), 1800);
  }

  const text = state === "copied" ? "Copiado" : state === "error" ? "No se pudo copiar" : "Copiar";

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={variant === "icon" ? `${label}: ${text.toLowerCase()}` : label}
      className={clsx(
        "inline-flex shrink-0 items-center gap-2 rounded-[4px] bg-surface-2 text-sm font-medium transition-colors duration-300",
        "hover:text-accent",
        state === "copied" && "text-ok hover:text-ok",
        variant === "pill" ? "h-9 px-3.5" : "h-9 w-9 justify-center",
        className,
      )}
    >
      <span className="relative grid h-4 w-4 place-items-center" aria-hidden>
        <AnimatePresence initial={false} mode="popLayout">
          {state === "copied" ? (
            <motion.span key="ok" initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }}>
              <Check size={16} strokeWidth={2.5} />
            </motion.span>
          ) : (
            <motion.span key="copy" initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }}>
              <Copy size={15} />
            </motion.span>
          )}
        </AnimatePresence>
      </span>
      {variant === "pill" && <span>{text}</span>}
      <span role="status" aria-live="polite" className="sr-only">
        {state === "copied" ? "Copiado al portapapeles" : state === "error" ? "No se pudo copiar al portapapeles" : ""}
      </span>
    </button>
  );
}
