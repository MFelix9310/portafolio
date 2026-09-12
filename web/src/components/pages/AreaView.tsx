import { Suspense } from 'react';
import { notFound } from 'next/navigation';

import AreaCatalog from '@/components/catalog/AreaCatalog';
import LayerChips from '@/components/catalog/LayerChips';
import LayerProvider from '@/components/catalog/LayerState';
import ProjectGrid from '@/components/catalog/ProjectGrid';
import Annotation from '@/components/primitives/Annotation';
import DimensionLine from '@/components/primitives/DimensionLine';
import Reveal from '@/components/motion/Reveal';
import { getArea, getProjectsByArea } from '@/lib/api/catalog';
import { copy, plural } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';
import type { AreaKey } from '@/lib/api/types';

interface AreaViewProps {
  areaKey: AreaKey;
  locale: Locale;
}

/** Vista filtrada del catálogo único (D4): las tres áreas comparten esta plantilla. */
export async function AreaView({ areaKey, locale }: AreaViewProps) {
  const c = copy(locale);
  const area = await getArea(areaKey);
  if (!area) notFound();

  const projects = await getProjectsByArea(areaKey);

  return (
    <div className="lamina py-12 md:py-16">
      <Reveal stagger="[data-head]" as="header" className="mb-10 flex flex-col gap-5">
        <Annotation data-head leader>
          {area.label} · {c.chrome.areas_index.heading}
        </Annotation>
        <h1
          data-head
          className="font-display text-display-md font-semibold text-content"
        >
          {localize(area.name, locale)}
        </h1>
        <p data-head className="max-w-prose text-base leading-relaxed text-muted md:text-lg">
          {localize(area.intro, locale)}
        </p>
        <div data-head className="max-w-md">
          <DimensionLine
            value={projects.length}
            label={plural(projects.length, c.chrome.layers.projects_one, c.chrome.layers.projects)}
            locale={locale}
            accent
          />
        </div>
      </Reveal>

      <LayerProvider>
        <div className="flex flex-col gap-8">
          {/* `useSearchParams` obliga a un límite de Suspense, así que sólo el
              conmutador de capas queda dentro: la rejilla se prerenderiza fuera y
              sus tarjetas van en el HTML servido. El fallback es la misma barra
              sin manejadores, para que el HTML estático ya la traiga y no haya
              salto al hidratar. */}
          <Suspense
            fallback={
              <LayerChips
                subareas={area.subareas}
                active={area.subareas.map((subarea) => subarea.key)}
                visible={projects.length}
                total={projects.length}
                locale={locale}
              />
            }
          >
            <AreaCatalog area={area} projects={projects} locale={locale} />
          </Suspense>

          <ProjectGrid projects={projects} areaKey={area.key} locale={locale} />
        </div>
      </LayerProvider>
    </div>
  );
}

export default AreaView;
