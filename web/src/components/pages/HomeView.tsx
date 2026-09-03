import Image from 'next/image';
import Link from 'next/link';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import DimensionLine from '@/components/primitives/DimensionLine';
import Reveal from '@/components/motion/Reveal';
import { getCatalog } from '@/lib/api/catalog';
import { copy, plural } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';
import { route, type RouteKey } from '@/lib/routes';

/**
 * Años en datos, contados desde la primera experiencia del catálogo. Nunca es un
 * literal: dentro de tres meses el número tiene que seguir siendo cierto solo.
 */
function yearsInData(startDates: string[]): number {
  const earliest = startDates
    .map((date) => new Date(date).getTime())
    .filter((time) => !Number.isNaN(time))
    .sort((a, b) => a - b)[0];
  if (earliest === undefined) return 0;
  return Math.round(((Date.now() - earliest) / (1000 * 60 * 60 * 24 * 365.25)) * 10) / 10;
}

/** El titular lleva la segunda mitad —«de obra a datos»— en rojo de revisión. */
/**
 * El titular se parte para acentuar la segunda mitad en rojo revision. El corte
 * lo marca el separador del propio texto: antes era un guion largo y ahora es
 * dos puntos, porque el copy los tiene prohibidos. Se aceptan ambos para que un
 * cambio de puntuacion no vuelva a dejar el titular sin acento.
 */
function splitHeadline(headline: string): [string, string | null] {
  const index = headline.search(/[:—]/);
  if (index === -1) return [headline, null];
  return [headline.slice(0, index).trim(), headline.slice(index + 1).trim()];
}

/** La tesis son dos frases; se rompen por la suya para que el paralelismo se vea. */
function splitThesis(thesis: string): string[] {
  const parts = thesis.split(/(?<=\.)\s+/).filter(Boolean);
  return parts.length > 1 ? parts : [thesis];
}

export async function HomeView({ locale }: { locale: Locale }) {
  const c = copy(locale);
  const catalog = await getCatalog();
  const years = yearsInData(catalog.experiences.map((item) => item.startDate));
  const [lead, accent] = splitHeadline(c.home.headline);
  const thesis = splitThesis(c.chrome.thesis);

  return (
    <>
      <section className="lamina relative pb-16 pt-16 md:pb-24 md:pt-24">
        <Reveal stagger="[data-hero]" as="header">
          <Annotation data-hero leader className="mb-8">
            {c.chrome.eyebrow}
          </Annotation>

          {/* Primero quién es y qué hace. El titular rompe el margen derecho:
              una acotación que sale del dibujo es intencional. */}
          <h1
            data-hero
            className="mb-8 max-w-[16ch] font-display text-display-lg font-semibold text-content md:-mr-8"
          >
            {lead}
            {accent ? (
              <>
                {' '}
                {/* El guion largo a 7 rem parece un filete suelto: se baja a
                    proporción de guion y se mantiene en el flujo del texto. */}
                <span className="align-middle text-[0.42em] text-faint">—</span>{' '}
                <span className="text-accent-text">{accent}</span>
              </>
            ) : null}
          </h1>

          {/* La tesis del sitio, en segundo plano pero sin perderse: explica por
              qué esto está dibujado como un plano. */}
          <p
            data-hero
            className="mb-8 border-l-2 border-accent pl-4 font-display text-display-sm font-medium leading-tight text-muted"
          >
            {thesis.map((sentence, index) => (
              <span key={sentence} className="block">
                {index === thesis.length - 1 ? (
                  <span className="text-content">{sentence}</span>
                ) : (
                  sentence
                )}
              </span>
            ))}
          </p>

          {/* El retrato entra aquí y no junto al titular, que rompe el margen
              derecho a propósito. Va como una lámina pegada al plano: filete,
              marcas de esquina y su rótulo en mono, nunca un avatar redondo. */}
          <div className="grid gap-8 md:grid-cols-[minmax(0,1fr)_auto] md:items-start md:gap-12">
            <div>
              <p className="max-w-prose text-base leading-relaxed text-content md:text-lg">
                {c.home.intro}
              </p>

              <Annotation as="p" className="mt-6 max-w-prose !normal-case !tracking-normal">
                {c.home.subtitle}
              </Annotation>
            </div>

            <figure data-hero className="order-first w-40 shrink-0 md:order-none md:w-52">
              <div className="relative border filete p-2">
                <CornerTicks size={10} className="text-accent" />
                <Image
                  src={catalog.profile.photo ?? ''}
                  alt={catalog.profile.name}
                  width={512}
                  height={512}
                  sizes="(min-width: 768px) 13rem, 10rem"
                  priority
                  className="block w-full"
                />
              </div>
              <figcaption className="mt-2 flex items-baseline justify-between gap-2">
                <Annotation className="!text-[0.625rem]">{catalog.profile.name}</Annotation>
                <span aria-hidden="true" className="h-px flex-1 bg-current text-faint opacity-40" />
              </figcaption>
            </figure>
          </div>
        </Reveal>
      </section>

      {/* Banda de medición: el gesto 1 en su forma más literal. */}
      <section aria-label={c.chrome.measure} className="lamina border-y filete py-8">
        <div className="grid gap-6 md:grid-cols-3">
          <DimensionLine
            value={catalog.projects.length}
            label={plural(catalog.projects.length, c.chrome.metrics.projects_one, c.chrome.metrics.projects)}
            locale={locale}
            accent
          />
          <DimensionLine
            value={years}
            decimals={1}
            label={c.chrome.metrics.years_in_data}
            locale={locale}
          />
          <DimensionLine
            value={catalog.areas.length}
            label={c.chrome.metrics.areas}
            locale={locale}
          />
        </div>
      </section>

      <section aria-labelledby="areas" className="lamina py-16 md:py-24">
        <div className="mb-8 flex flex-wrap items-baseline justify-between gap-4">
          <h2 id="areas" className="font-display text-display-sm font-semibold text-content">
            {c.chrome.areas_index.heading}
          </h2>
          <Annotation leader>{c.chrome.areas_index.note}</Annotation>
        </div>

        <Reveal stagger="[data-area]" as="ul" className="flex flex-col border-t filete">
          {catalog.areas.map((area) => (
            <li key={area.key} data-area>
              <Link
                href={route(area.key as RouteKey, locale)}
                className="group relative grid grid-cols-[auto_1fr] items-start gap-x-6 gap-y-3 border-b filete py-8 md:grid-cols-[4rem_1fr_auto] md:py-10"
              >
                <CornerTicks
                  size={12}
                  top
                  className="text-accent opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                />
                <span className="font-mono text-note-lg tabular-nums text-faint">
                  {area.label}
                </span>

                <span className="flex flex-col gap-2">
                  <span className="font-display text-2xl font-semibold leading-none tracking-tight text-content transition-transform duration-500 ease-cota group-hover:translate-x-1 md:text-4xl">
                    {localize(area.name, locale)}
                  </span>
                  <span className="max-w-prose text-sm leading-relaxed text-muted">
                    {localize(area.blurb, locale)}
                  </span>
                </span>

                <span className="col-start-2 flex items-center gap-3 md:col-start-3 md:self-center">
                  <Annotation className="tabular-nums">
                    {String(area.count).padStart(2, '0')}{' '}
                    {plural(area.count, c.chrome.layers.projects_one, c.chrome.layers.projects)}
                  </Annotation>
                  <span
                    aria-hidden="true"
                    className="h-px w-8 bg-accent transition-transform duration-500 ease-cota group-hover:scale-x-150"
                    style={{ transformOrigin: 'left center' }}
                  />
                </span>
              </Link>
            </li>
          ))}
        </Reveal>
      </section>
    </>
  );
}

export default HomeView;
