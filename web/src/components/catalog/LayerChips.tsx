import Annotation from '@/components/primitives/Annotation';
import type { Subarea } from '@/lib/api/types';
import { copy, plural } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';

interface LayerChipsProps {
  subareas: Subarea[];
  active: string[];
  /** Proyectos dibujados y proyectos del área, para el contador del cajetín. */
  visible: number;
  total: number;
  locale: Locale;
  /**
   * Sin manejadores la barra es el rótulo estático que el servidor mete en el
   * HTML: mismo marcado, mismas medidas, sin interacción. Con ellos es el
   * conmutador hidratado. Que sea el mismo componente evita el salto al hidratar.
   */
  onToggle?: (key: string) => void;
  onReset?: () => void;
}

const pad = (value: number) => String(value).padStart(2, '0');

/**
 * Conmutador de capas, no filtros de e-commerce. Cada chip es una capa del mismo
 * plano: encendida se dibuja, apagada queda su rótulo tachado y su contenido
 * fuera de la lámina. El contador va dentro de la misma barra porque es el
 * cajetín de lo que se está viendo.
 */
export function LayerChips({
  subareas,
  active,
  visible,
  total,
  locale,
  onToggle,
  onReset,
}: LayerChipsProps) {
  const c = copy(locale);
  const allOn = active.length === subareas.length;

  const chipClass = (on: boolean) =>
    `group flex items-center gap-2 border px-2.5 py-1.5 font-mono text-note uppercase tracking-[0.14em] transition-colors duration-200 ${
      on ? 'border-content/45 text-content' : 'filete text-faint hover:text-muted'
    }`;

  return (
    <div className="flex flex-col gap-3 border-y filete py-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <Annotation leader>{c.chrome.layers.label}</Annotation>
        <p className="sr-only">{c.chrome.layers.help}</p>
        {subareas.map((subarea) => {
          const on = active.includes(subarea.key);
          const face = (
            <>
              <span
                aria-hidden="true"
                className={`block h-2 w-2 border border-current ${on ? 'bg-accent' : 'bg-transparent'}`}
              />
              <span className={on ? '' : 'line-through decoration-1'}>
                {localize(subarea.name, locale)}
              </span>
              <span className="tabular-nums opacity-60">{pad(subarea.count)}</span>
            </>
          );

          return onToggle ? (
            <button
              key={subarea.key}
              type="button"
              aria-pressed={on}
              onClick={() => onToggle(subarea.key)}
              className={chipClass(on)}
            >
              {face}
            </button>
          ) : (
            <span key={subarea.key} className={chipClass(on)}>
              {face}
            </span>
          );
        })}
      </div>

      {onReset && !allOn ? (
        <button
          type="button"
          onClick={onReset}
          className="self-start font-mono text-note uppercase tracking-[0.14em] text-accent-text underline underline-offset-4"
        >
          {c.chrome.layers.reset}
        </button>
      ) : null}

      <Annotation aria-live="polite">
        {c.chrome.layers.showing} {pad(visible)} {c.chrome.layers.of} {pad(total)}{' '}
        {plural(total, c.chrome.layers.projects_one, c.chrome.layers.projects)}
      </Annotation>
    </div>
  );
}

export default LayerChips;
