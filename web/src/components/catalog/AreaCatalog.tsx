'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useMemo } from 'react';

import LayerChips from './LayerChips';
import ProjectGrid from './ProjectGrid';
import Annotation from '@/components/primitives/Annotation';
import type { Area, Project } from '@/lib/api/types';
import { copy, plural } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';

interface AreaCatalogProps {
  area: Area;
  projects: Project[];
  locale: Locale;
}

/**
 * Estado de las capas en la URL (`?subarea=scientist,analyst`), no en memoria:
 * el filtro se comparte, se marca y se navega con el botón atrás.
 * Sin el parámetro, todas las capas están encendidas.
 */
export function AreaCatalog({ area, projects, locale }: AreaCatalogProps) {
  const c = copy(locale);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const allKeys = useMemo(() => area.subareas.map((subarea) => subarea.key), [area.subareas]);
  const raw = searchParams.get('subarea');

  const active = useMemo(() => {
    if (raw === null) return allKeys;
    return raw
      .split(',')
      .map((key) => key.trim())
      .filter((key) => allKeys.includes(key));
  }, [raw, allKeys]);

  const write = (next: string[]) => {
    const params = new URLSearchParams(searchParams.toString());
    if (next.length === allKeys.length) params.delete('subarea');
    else params.set('subarea', next.join(','));
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  const toggle = (key: string) => {
    write(active.includes(key) ? active.filter((item) => item !== key) : [...active, key]);
  };

  const visible = useMemo(
    () =>
      projects.filter((project) =>
        project.tags.some((tag) => tag.area === area.key && active.includes(tag.subarea)),
      ),
    [projects, active, area.key],
  );

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3 border-y filete py-4">
        <LayerChips
          subareas={area.subareas}
          active={active}
          locale={locale}
          onToggle={toggle}
          onReset={() => write(allKeys)}
        />
        <Annotation aria-live="polite">
          {c.chrome.layers.showing} {String(visible.length).padStart(2, '0')} {c.chrome.layers.of}{' '}
          {String(projects.length).padStart(2, '0')}{' '}
          {plural(projects.length, c.chrome.layers.projects_one, c.chrome.layers.projects)}
        </Annotation>
      </div>

      {visible.length > 0 ? (
        <ProjectGrid projects={visible} locale={locale} />
      ) : (
        <p className="border filete p-8 text-center font-mono text-note uppercase tracking-[0.14em] text-muted">
          {c.chrome.layers.all_off}
        </p>
      )}
    </div>
  );
}

export default AreaCatalog;
