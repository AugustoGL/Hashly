"use client";

import { useSyncExternalStore } from "react";

const reducedQuery = "(prefers-reduced-motion: reduce)";

function subscribeReduced(cb: () => void) {
  const mq = window.matchMedia(reducedQuery);
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}

/** true si el usuario pidió menos movimiento. En el servidor asume que sí (no hay animación hasta hidratar). */
export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(
    subscribeReduced,
    () => window.matchMedia(reducedQuery).matches,
    () => true,
  );
}

/**
 * true si hay WebGL acelerado por GPU. Con renderizado por software
 * (SwiftShader, llvmpipe: aceleración desactivada, sin drivers, VMs) la escena
 * de partículas se comería la CPU, así que en esos casos se usan las imágenes fijas.
 */
export function hasHardwareWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    const gl = (canvas.getContext("webgl2") || canvas.getContext("webgl")) as WebGLRenderingContext | null;
    if (!gl) return false;
    const info = gl.getExtension("WEBGL_debug_renderer_info");
    const renderer = info ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)) : "";
    gl.getExtension("WEBGL_lose_context")?.loseContext();
    return !/swiftshader|llvmpipe|software|basic render/i.test(renderer);
  } catch {
    return false;
  }
}
