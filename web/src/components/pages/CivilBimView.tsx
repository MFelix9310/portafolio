import EmptyArea from '@/components/catalog/EmptyArea';
import ExtrusionSlot from '@/components/civil/ExtrusionSlot';
import Annotation from '@/components/primitives/Annotation';
import Reveal from '@/components/motion/Reveal';
import { getArea, getProjectsByArea } from '@/lib/api/catalog';
import AreaCatalog from '@/components/catalog/AreaCatalog';
import LayerChips from '@/components/catalog/LayerChips';
import LayerProvider from '@/components/catalog/LayerState';
import ProjectGrid from '@/components/catalog/ProjectGrid';
import { copy } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';
import { Suspense } from 'react';

/**
 * `/civil-bim` nace con cero proyectos (D4) y así sigue hasta que Félix los suba
 * desde el panel. Cuando los haya, esta misma vista los pinta con el catálogo
 * normal — el vacío es un estado, no una página distinta.
 */
export async function CivilBimView({ locale }: { locale: Locale }) {
  const c = copy(locale);
  const area = await getArea('civil-bim');
  const projects = await getProjectsByArea('civil-bim');
  if (!area) return null;

  return (
    <div className="lamina py-12 md:py-16">
      <Reveal stagger="[data-head]" as="header" className="mb-10 flex flex-col gap-5">
        <Annotation data-head leader>
          {area.label} · {c.chrome.areas_index.heading}
        </Annotation>
        <h1 data-head className="font-display text-display-md font-semibold text-content">
          {localize(area.name, locale)}
        </h1>
        <p data-head className="max-w-prose text-base leading-relaxed text-muted md:text-lg">
          {localize(area.intro, locale)}
        </p>
      </Reveal>

      {/* Hueco del gesto 4 (extrusión 3D). Ver ExtrusionPlaceholder. */}
      <div className="mb-12">
        <ExtrusionSlot locale={locale} />
      </div>

      {projects.length === 0 ? (
        <EmptyArea locale={locale} sheet="C-01" />
      ) : (
        <LayerProvider>
          <div className="flex flex-col gap-8">
            {/* Igual que en AreaView: dentro del Suspense sólo va el conmutador,
                que es lo único que lee la URL. La rejilla se prerenderiza. */}
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
      )}
    </div>
  );
}

export default CivilBimView;
