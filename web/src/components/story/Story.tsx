"use client";

import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { hasHardwareWebGL } from "@/lib/hooks";
import { sha256Hex } from "@/lib/merkle";
import type { Engine } from "../scene/engine";

gsap.registerPlugin(ScrollTrigger);

export const HERO_LINE = "Probá que existía.";

const steps = [
  {
    title: "Primero, tu archivo",
    body: "Un contrato en PDF, las fotos de una obra, un acta. Lo elegís vos y Hashly no lo guarda.",
  },
  {
    title: "Después, su huella",
    body: "El archivo se reduce a un hash SHA-256: 64 caracteres que cambian por completo si cambia un solo byte. Estas 64 barras son la huella de la frase de arriba.",
  },
  {
    title: "Luego, el árbol",
    body: "Las huellas se combinan de a pares hasta quedar una sola. Hojas y nodos llevan prefijos distintos (RFC 6962), así ninguno puede hacerse pasar por otro.",
  },
  {
    title: "Entonces, una raíz",
    body: "Un único merkle_root de 32 bytes representa a todos tus archivos juntos. Es lo único que se sella.",
  },
  {
    title: "Al final, el sello",
    body: "La raíz entra en un bloque de Bitcoin con OpenTimestamps. En unas horas tenés una prueba .ots que no depende de nosotros.",
  },
  {
    title: "Y siempre, la verificación",
    body: "Cualquiera vuelve a hashear el archivo, recorre el camino hasta la raíz y la compara con la sellada. Si coincide, existía así desde esa fecha.",
  },
];

type Mode = "loading" | "live" | "still";

/**
 * Hero + "Cómo funciona" en un solo escenario:
 * el canvas WebGPU se ve primero por la ventana dentro de la frase; al bajar,
 * la ventana se abre a pantalla completa y las partículas cuentan la historia.
 */
export function Story() {
  const wrapper = useRef<HTMLDivElement>(null);
  const hero = useRef<HTMLElement>(null);
  const frame = useRef<HTMLDivElement>(null);
  const layer = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const left = useRef<HTMLSpanElement>(null);
  const right = useRef<HTMLSpanElement>(null);
  const aside = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLOListElement>(null);
  const engine = useRef<Engine | null>(null);
  const debugStageRef = useRef<number | null>(null);
  const [mode, setMode] = useState<Mode>("loading");
  const [active, setActive] = useState(0);

  // Arranque del motor: solo con GPU real y sin reduced motion. `?escena` lo fuerza (depuración).
  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams(window.location.search);
    const forced = params.has("escena");
    // `?n=8192` baja la cantidad de partículas (para revisar en navegadores sin GPU).
    const countParam = Number(params.get("n")) || 0;
    const debugStage = params.has("etapa") ? Number(params.get("etapa")) : null;
    debugStageRef.current = debugStage;
    // Se lee directo del navegador: el hook arranca en "reducido" durante la hidratación.
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced || !(forced || hasHardwareWebGL()) || !canvas.current) {
      queueMicrotask(() => !cancelled && setMode("still"));
      return;
    }
    (async () => {
      try {
        const [{ createEngine }, hashHex] = await Promise.all([
          import("../scene/engine"),
          sha256Hex(new TextEncoder().encode(HERO_LINE)),
        ]);
        if (cancelled || !canvas.current) return;
        const mobile = window.matchMedia("(max-width: 767px)").matches;
        engine.current = await createEngine(canvas.current, {
          count: countParam || (mobile ? 32768 : 131072),
          hashHex,
          mobile,
          // `?etapa=3` arranca con esa forma ya armada y la deja fija (depuración y capturas).
          initialStage: debugStage ?? 0,
        });
        if (!cancelled) setMode("live");
      } catch (error) {
        console.warn("[hashly] escena 3D no disponible, se usa la versión estática", error);
        if (!cancelled) setMode("still");
      }
    })();
    return () => {
      cancelled = true;
      engine.current?.dispose();
      engine.current = null;
    };
  }, []);

  // Puntero y giroscopio mueven la escena.
  useEffect(() => {
    if (mode !== "live") return;
    const onMove = (e: PointerEvent) =>
      engine.current?.setPointer((e.clientX / window.innerWidth) * 2 - 1, -((e.clientY / window.innerHeight) * 2 - 1));
    const onTilt = (e: DeviceOrientationEvent) => {
      if (e.gamma == null || e.beta == null) return;
      engine.current?.setTilt(Math.max(-1, Math.min(1, e.gamma / 30)), Math.max(-1, Math.min(1, (45 - e.beta) / 30)));
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("deviceorientation", onTilt, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("deviceorientation", onTilt);
    };
  }, [mode]);

  // Coreografía de scroll.
  useEffect(() => {
    if (mode === "loading") return;
    const ctx = gsap.context(() => {
      const mobile = () => window.innerWidth < 768;
      const storyLayout = () => (mobile() ? ([0, 0.9, 0.62] as const) : ([2.05, 0, 0.72] as const));

      // 1. La ventana se abre.
      const open = (p: number) => {
        const e = gsap.parseEase("power2.inOut")(p);
        const f = frame.current?.getBoundingClientRect();
        if (f && layer.current) {
          const vw = window.innerWidth;
          const vh = window.innerHeight;
          const k = 1 - e;
          layer.current.style.clipPath = `inset(${f.top * k}px ${(vw - f.right) * k}px ${(vh - f.bottom) * k}px ${f.left * k}px round ${6 * k}px)`;
        }
        const spread = mobile() ? 0 : e * 22;
        if (left.current) left.current.style.transform = `translate3d(${-spread}vw, 0, 0)`;
        if (right.current) right.current.style.transform = `translate3d(${spread}vw, 0, 0)`;
        const fade = Math.max(0, 1 - e * 1.6);
        [left.current, right.current, aside.current].forEach((el) => el && (el.style.opacity = String(fade)));
        if (engine.current && mode === "live" && f && debugStageRef.current === null) {
          // Al principio la escena se encuadra en la ventana; al abrirse, pasa a su lugar de la historia.
          const vw = window.innerWidth;
          const vh = window.innerHeight;
          const halfH = engine.current.viewHalfHeight();
          const halfW = halfH * (vw / vh);
          const fx = ((f.left + f.width / 2) / vw) * 2 - 1;
          const fy = 1 - ((f.top + f.height / 2) / vh) * 2;
          // El cristal con sus anillos mide ~5,6 unidades: que ocupe el 85 % del alto de la ventana.
          const fitScale = ((f.height / vh) * 2 * halfH * 0.85) / 5.6;
          const [x, y, s] = storyLayout();
          engine.current.setStage(p);
          engine.current.setLayout(fx * halfW + (x - fx * halfW) * e, fy * halfH + (y - fy * halfH) * e, fitScale + (s - fitScale) * e);
        }
      };

      ScrollTrigger.create({
        trigger: hero.current,
        start: "top top",
        end: "bottom bottom",
        onUpdate: (self) => open(self.progress),
        onRefresh: (self) => open(self.progress),
      });

      // 2. La historia: la etapa llega a su forma cuando su texto está centrado.
      const n = steps.length;
      ScrollTrigger.create({
        trigger: list.current,
        start: "top center",
        end: "bottom center",
        onUpdate: (self) => {
          const p = self.progress;
          setActive(Math.min(n - 1, Math.floor(p * n)));
          if (mode === "live" && p > 0 && debugStageRef.current === null) engine.current?.setStage(1 + gsap.utils.clamp(0, n - 1, p * n - 0.5));
        },
      });

      // 3. Fuera del escenario, la GPU descansa.
      ScrollTrigger.create({
        trigger: wrapper.current,
        start: "top bottom",
        end: "bottom top",
        onToggle: (self) => engine.current?.setRunning(self.isActive),
      });
    }, wrapper);
    return () => ctx.revert();
  }, [mode]);

  const live = mode !== "still";

  return (
    <div ref={wrapper} className="relative">
      {/* Capa del canvas: fija mientras dura el escenario, recortada a la ventana al principio. */}
      <div className="pointer-events-none sticky top-0 -mb-[100svh] h-[100svh]" aria-hidden>
        <div
          ref={layer}
          className={clsx("absolute inset-0 transition-opacity duration-700", mode === "live" ? "opacity-100" : "opacity-0")}
          style={{ clipPath: "inset(50% 50% 50% 50%)" }}
        >
          <canvas ref={canvas} className="block h-full w-full" />
        </div>
      </div>

      {/* Hero */}
      <section ref={hero} aria-labelledby="hero-title" className={clsx("relative", live ? "h-[210svh]" : "h-auto")}>
        <div className={clsx("frame-x flex flex-col", live ? "sticky top-0 h-[100svh]" : "min-h-[100svh]")}>
          <h1 id="hero-title" className="display relative flex flex-1 flex-col justify-center gap-4 pt-24 text-[clamp(3.6rem,14vw,6rem)] md:flex-row md:items-center md:justify-between md:gap-[2vw] md:pt-0 md:text-[length:var(--step-display)]">
            <span ref={left} className="block will-change-transform">
              Probá que
            </span>
            {/* La ventana: el canvas se ve a través de ella. */}
            <span
              ref={frame}
              aria-hidden
              className={clsx(
                "relative block aspect-[4/3] w-full shrink-0 overflow-hidden rounded-[6px] md:aspect-video md:w-[34vw]",
                mode === "live" ? "bg-transparent" : "bg-surface",
              )}
            >
              {mode === "still" && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src="/stages/0.webp" alt="" className="h-full w-full object-cover" width={1600} height={900} />
              )}
            </span>
            <span ref={right} className="block self-end will-change-transform md:self-auto">
              existía.
            </span>
          </h1>
          <div ref={aside} className="flex flex-col gap-6 pb-10 md:flex-row md:items-end md:justify-between md:pb-12">
            <p className="max-w-[34rem] text-[length:var(--step-lead)] leading-snug">
              Hashly sella la huella de tus archivos en Bitcoin. Cualquiera puede verificar la fecha; nadie puede ver el archivo.
            </p>
            <a href="#probalo" className="btn btn-accent self-start md:self-auto">
              Probar la demo
            </a>
          </div>
        </div>
      </section>

      {/* Cómo funciona */}
      <section id="como-funciona" aria-labelledby="story-title" className="relative">
        <h2 id="story-title" className="sr-only">
          Cómo funciona
        </h2>
        <ol ref={list} className="frame-x relative">
          {steps.map((step, i) => (
            <li
              key={step.title}
              aria-current={active === i ? "step" : undefined}
              className={clsx(
                "flex md:items-center",
                // Con la escena, cada paso dura una pantalla; sin ella, la imagen fija no necesita tanto recorrido.
                live ? "min-h-[100svh] items-end pb-[8svh]" : "flex-col justify-center gap-8 py-12 md:flex-row md:justify-between",
              )}
            >
              <div
                className={clsx(
                  "max-w-[30rem]",
                  // En móvil el texto va sobre la escena: un velo neutro lo hace legible.
                  live && "-mx-[var(--margin)] bg-bg/85 px-[var(--margin)] py-6 md:mx-0 md:bg-transparent md:p-0",
                )}
              >
                <h3 className="head text-[length:var(--step-head)]">{step.title}</h3>
                <p className="mt-5 text-[length:var(--step-body)] leading-relaxed text-ink">{step.body}</p>
              </div>
              {mode === "still" && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`/stages/${i + 1}.webp`}
                  alt=""
                  width={1600}
                  height={900}
                  loading="lazy"
                  className="aspect-video w-full rounded-[6px] bg-surface object-cover md:w-[52%]"
                />
              )}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
