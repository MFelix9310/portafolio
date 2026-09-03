'use client';

import { useEffect, useRef, type ReactNode } from 'react';

import { EASE, ensureGsap, prefersReducedMotion } from '@/lib/motion';

/**
 * Segunda mitad del gesto 3. La tarjeta dibuja una marca de sección al pulsarla;
 * aquí el detalle crece desde esa marca, como el despiece ampliado de un plano.
 */
export function DetailEntrance({ children }: { children: ReactNode }) {
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = root.current;
    if (!element || prefersReducedMotion()) return;

    const gsap = ensureGsap();
    const context = gsap.context(() => {
      gsap
        .timeline()
        .fromTo(
          '[data-detail-mark]',
          { scaleX: 0, autoAlpha: 1 },
          { scaleX: 1, duration: 0.3, ease: 'power2.inOut' },
        )
        .fromTo(
          '[data-detail-body]',
          { autoAlpha: 0, scaleY: 0.985, y: 10 },
          { autoAlpha: 1, scaleY: 1, y: 0, duration: 0.5, ease: EASE },
          '-=0.12',
        )
        .to('[data-detail-mark]', { autoAlpha: 0, duration: 0.3 }, '-=0.2');
    }, element);

    return () => context.revert();
  }, []);

  return (
    <div ref={root} className="relative">
      <span
        data-detail-mark
        aria-hidden="true"
        className="pointer-events-none absolute left-0 top-0 h-px w-full bg-accent opacity-0"
        style={{ transformOrigin: 'center' }}
      />
      <div data-detail-body style={{ transformOrigin: 'top center' }}>
        {children}
      </div>
    </div>
  );
}

export default DetailEntrance;
