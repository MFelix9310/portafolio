'use client';

import Annotation from '@/components/primitives/Annotation';
import type { Subarea } from '@/lib/api/types';
import { copy } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';

interface LayerChipsProps {
  subareas: Subarea[];
  active: string[];
  locale: Locale;
  onToggle: (key: string) => void;
  onReset: () => void;
}

/**
 * Conmutador de capas, no filtros de e-commerce. Cada chip es una capa del mismo
 * plano: encendida se dibuja, apagada queda su rótulo tachado y su contenido
 * fuera de la lámina.
 */
export function LayerChips({ subareas, active, locale, onToggle, onReset }: LayerChipsProps) {
  const c = copy(locale);
  const allOn = active.length === subareas.length;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <Annotation leader>{c.chrome.layers.label}</Annotation>
        <p className="sr-only">{c.chrome.layers.help}</p>
        {subareas.map((subarea) => {
          const on = active.includes(subarea.key);
          return (
            <button
              key={subarea.key}
              type="button"
              aria-pressed={on}
              onClick={() => onToggle(subarea.key)}
              className={`group flex items-center gap-2 border px-2.5 py-1.5 font-mono text-note uppercase tracking-[0.14em] transition-colors duration-200 ${
                on
                  ? 'border-content/45 text-content'
                  : 'filete text-faint hover:text-muted'
              }`}
            >
              <span
                aria-hidden="true"
                className={`block h-2 w-2 border border-current ${on ? 'bg-accent' : 'bg-transparent'}`}
              />
              <span className={on ? '' : 'line-through decoration-1'}>
                {localize(subarea.name, locale)}
              </span>
              <span className="tabular-nums opacity-60">{String(subarea.count).padStart(2, '0')}</span>
            </button>
          );
        })}
      </div>

      {!allOn ? (
        <button
          type="button"
          onClick={onReset}
          className="self-start font-mono text-note uppercase tracking-[0.14em] text-accent-text underline underline-offset-4"
        >
          {c.chrome.layers.reset}
        </button>
      ) : null}
    </div>
  );
}

export default LayerChips;
