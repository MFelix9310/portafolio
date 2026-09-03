'use client';

import Lenis from 'lenis';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

import { ScrollTrigger, ensureGsap, prefersReducedMotion } from '@/lib/motion';

/**
 * Scroll suavizado con Lenis, con GSAP como único reloj para que ScrollTrigger y
 * el scroll no se desincronicen.
 *
 * Con `prefers-reduced-motion` no se instancia nada: ni Lenis, ni ScrollTrigger.
 * El navegador conserva su scroll nativo y las animaciones no llegan a existir.
 */
export function SmoothScroll() {
  const pathname = usePathname();

  useEffect(() => {
    if (prefersReducedMotion()) return;

    const gsap = ensureGsap();
    const lenis = new Lenis({ lerp: 0.09, wheelMultiplier: 0.9 });

    const update = () => ScrollTrigger.update();
    lenis.on('scroll', update);

    const tick = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);

    return () => {
      lenis.off('scroll', update);
      gsap.ticker.remove(tick);
      lenis.destroy();
    };
  }, []);

  // Cada navegación reinicia el scroll y recalcula los disparadores del documento nuevo.
  useEffect(() => {
    if (prefersReducedMotion()) return;
    window.scrollTo(0, 0);
    const id = window.setTimeout(() => ScrollTrigger.refresh(), 120);
    return () => window.clearTimeout(id);
  }, [pathname]);

  return null;
}

export default SmoothScroll;
