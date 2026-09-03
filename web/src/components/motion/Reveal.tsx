'use client';

import { useEffect, useRef, type ReactNode } from 'react';

import { EASE, ensureGsap, prefersReducedMotion } from '@/lib/motion';

interface RevealProps {
  children: ReactNode;
  /** Selector de hijos a escalonar. Sin él se anima el bloque entero. */
  stagger?: string;
  delay?: number;
  className?: string;
  as?: 'div' | 'section' | 'ul' | 'header';
}

/**
 * Aparición por scroll. Sólo `transform` y `opacity`, nunca nada que dispare
 * layout. El estado inicial se aplica desde JS, así que si el script no llega el
 * contenido ya está visible en su estado final.
 */
export function Reveal({
  children,
  stagger,
  delay = 0,
  className = '',
  as: Tag = 'div',
}: RevealProps) {
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = root.current;
    if (!element || prefersReducedMotion()) return;

    const gsap = ensureGsap();
    const context = gsap.context(() => {
      const targets = stagger ? element.querySelectorAll(stagger) : [element];
      if (!targets.length) return;
      gsap.fromTo(
        targets,
        { autoAlpha: 0, y: 18 },
        {
          autoAlpha: 1,
          y: 0,
          duration: 0.65,
          ease: EASE,
          delay,
          stagger: stagger ? 0.07 : 0,
          scrollTrigger: { trigger: element, start: 'top 88%', once: true },
        },
      );
    }, element);

    return () => context.revert();
  }, [stagger, delay]);

  return (
    <Tag ref={root as never} className={className}>
      {children}
    </Tag>
  );
}

export default Reveal;
