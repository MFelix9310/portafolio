'use client';

import { useEffect, useRef } from 'react';

import { DUR, EASE, ScrollTrigger, ensureGsap, prefersReducedMotion } from '@/lib/motion';
import type { Locale } from '@/lib/i18n/locale';

interface DimensionLineProps {
  value: number;
  label: string;
  locale: Locale;
  decimals?: number;
  className?: string;
  /** Rojo de lápiz de revisión: sólo para la cota que el visitante debe leer primero. */
  accent?: boolean;
}

function format(value: number, decimals: number, locale: Locale) {
  return value.toLocaleString(locale === 'es' ? 'es-ES' : 'en-GB', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Gesto 1 — la acotación que mide.
 *
 * La línea se extiende desde el centro hacia los extremos y el número cuenta
 * hasta el valor real. El movimiento *es* el dato apareciendo, así que el estado
 * final está en el HTML: sin JS (o con `prefers-reduced-motion`) la cota ya está
 * dibujada y el número ya es el correcto.
 */
export function DimensionLine({
  value,
  label,
  locale,
  decimals = 0,
  className = '',
  accent = false,
}: DimensionLineProps) {
  const root = useRef<HTMLDivElement>(null);
  const counter = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const element = root.current;
    if (!element || prefersReducedMotion()) return;

    const gsap = ensureGsap();
    const context = gsap.context(() => {
      const timeline = gsap.timeline({
        scrollTrigger: { trigger: element, start: 'top 88%', once: true },
      });

      timeline
        .fromTo(
          element.querySelectorAll('[data-cota-line]'),
          { scaleX: 0 },
          { scaleX: 1, duration: DUR.draw, ease: EASE },
        )
        .fromTo(
          element.querySelectorAll('[data-cota-tick]'),
          { scaleY: 0 },
          { scaleY: 1, duration: DUR.tick, ease: EASE, stagger: 0.04 },
          '-=0.25',
        );

      const target = { v: 0 };
      timeline.to(
        target,
        {
          v: value,
          duration: DUR.count,
          ease: 'power2.out',
          onUpdate: () => {
            if (counter.current) counter.current.textContent = format(target.v, decimals, locale);
          },
          onComplete: () => {
            if (counter.current) counter.current.textContent = format(value, decimals, locale);
          },
        },
        0,
      );
    }, element);

    return () => {
      context.revert();
      ScrollTrigger.refresh();
    };
  }, [value, decimals, locale]);

  const tone = accent ? 'text-accent-text' : 'text-content';

  return (
    <div ref={root} className={`flex w-full items-center gap-2 ${tone} ${className}`}>
      <span
        data-cota-tick
        aria-hidden="true"
        className="h-3 w-px shrink-0 bg-current"
        style={{ transformOrigin: 'center' }}
      />
      <span aria-hidden="true" className="relative h-px flex-1">
        <span
          data-cota-line
          className="absolute inset-0 block bg-current"
          style={{ transformOrigin: 'right center' }}
        />
      </span>
      <span className="whitespace-nowrap font-mono text-note uppercase tracking-[0.14em]">
        <span ref={counter} className="tabular-nums">
          {format(value, decimals, locale)}
        </span>{' '}
        {label}
      </span>
      <span aria-hidden="true" className="relative h-px flex-1">
        <span
          data-cota-line
          className="absolute inset-0 block bg-current"
          style={{ transformOrigin: 'left center' }}
        />
      </span>
      <span
        data-cota-tick
        aria-hidden="true"
        className="h-3 w-px shrink-0 bg-current"
        style={{ transformOrigin: 'center' }}
      />
    </div>
  );
}

export default DimensionLine;
