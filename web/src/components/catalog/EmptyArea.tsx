import Link from 'next/link';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import DimensionLine from '@/components/primitives/DimensionLine';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';
import { route } from '@/lib/routes';

interface EmptyAreaProps {
  locale: Locale;
  sheet: string;
}

/**
 * El vacío de `/civil-bim` es contenido, no ausencia de contenido: una lámina en
 * blanco con su cajetín puesto y su sello de revisión. Dice exactamente lo que
 * pasa —el área existe, los proyectos aún no— en vez de disimularlo con relleno.
 */
export function EmptyArea({ locale, sheet }: EmptyAreaProps) {
  const c = copy(locale);
  const empty = c.areas.civil_bim.empty_state;

  return (
    <section aria-labelledby="lamina-vacia" className="relative">
      <div className="relative border filete bg-surface-sunken">
        <CornerTicks size={16} />

        {/* Cuadro de dibujo: vacío a propósito, con el sello encima. */}
        <div className="relative flex min-h-[42vh] items-center justify-center overflow-hidden p-8">
          <span
            aria-hidden="true"
            className="absolute inset-8 border border-dashed border-rule/25"
          />
          <p
            className="relative select-none font-display text-[clamp(5rem,18vw,12rem)] font-semibold leading-none tracking-tighter text-content/[0.07]"
            aria-hidden="true"
          >
            00
          </p>
          <span className="absolute right-6 top-8 -rotate-[7deg] border-2 border-accent px-4 py-2 font-mono text-note-lg uppercase tracking-[0.2em] text-accent-text md:right-16">
            {c.chrome.civil_bim.stamp}
          </span>
        </div>

        {/* Cajetín de la lámina. */}
        <div className="grid gap-6 border-t filete p-6 md:grid-cols-[1.4fr_1fr] md:p-8">
          <div className="flex flex-col gap-4">
            <h2 id="lamina-vacia" className="font-display text-display-sm font-semibold text-content">
              {empty.title}
            </h2>
            <p className="max-w-prose text-sm leading-relaxed text-muted md:text-base">
              {empty.body}
            </p>
            <Annotation leader accent>
              {c.chrome.civil_bim.note}
            </Annotation>
          </div>

          <div className="flex flex-col justify-between gap-6 border-t filete pt-6 md:border-l md:border-t-0 md:pl-8 md:pt-0">
            <DimensionLine value={0} label={c.chrome.layers.projects} locale={locale} accent />
            <div className="flex flex-col gap-3">
              <Annotation>{c.chrome.civil_bim.meanwhile}</Annotation>
              <p className="text-sm leading-relaxed text-muted">
                {c.chrome.civil_bim.meanwhile_body}
              </p>
              <div className="flex flex-wrap gap-3">
                <Link
                  href={route('data', locale)}
                  className="border filete px-3 py-2 font-mono text-note uppercase tracking-[0.14em] text-content transition-colors duration-200 hover:border-content/50 hover:bg-content hover:text-surface"
                >
                  {c.nav.areas.data}
                </Link>
                <Link
                  href={route('developer', locale)}
                  className="border filete px-3 py-2 font-mono text-note uppercase tracking-[0.14em] text-content transition-colors duration-200 hover:border-content/50 hover:bg-content hover:text-surface"
                >
                  {c.nav.areas.developer}
                </Link>
              </div>
            </div>
            <Annotation className="tabular-nums">
              {c.chrome.sheet.label} {sheet}
            </Annotation>
          </div>
        </div>
      </div>
    </section>
  );
}

export default EmptyArea;
