"use client";

import { useEffect } from "react";

/** Entradas por sección: cada [data-reveal] sube y aparece una vez, escalonado por --i. */
export function Reveal() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("is-in");
          observer.unobserve(entry.target);
        }
      },
      { rootMargin: "0px 0px -12% 0px" },
    );
    document.querySelectorAll("[data-reveal]").forEach((el) => observer.observe(el));
    // Red de seguridad: si se salta a mitad de página (un ancla, un scroll muy rápido),
    // todo lo que ya quedó arriba aparece aunque el observador no lo haya visto pasar.
    const onScroll = () => {
      document.querySelectorAll("[data-reveal]:not(.is-in)").forEach((el) => {
        if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add("is-in");
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
  }, []);
  return null;
}
