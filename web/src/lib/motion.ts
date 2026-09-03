import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

let registered = false;

/** Registra ScrollTrigger una sola vez y sólo en cliente. */
export function ensureGsap() {
  if (typeof window === 'undefined') return gsap;
  if (!registered) {
    gsap.registerPlugin(ScrollTrigger);
    registered = true;
  }
  return gsap;
}

export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return true;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export { gsap, ScrollTrigger };

/** Duraciones compartidas: el movimiento tiene que leerse como un trazo, no como un efecto. */
export const DUR = {
  tick: 0.22,
  draw: 0.7,
  count: 1.1,
  layer: 0.36,
} as const;

export const EASE = 'power3.out';
