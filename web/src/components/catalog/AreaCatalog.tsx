'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useRef } from 'react';

import LayerChips from './LayerChips';
import { useLayers } from './LayerState';
import type { Area, Project } from '@/lib/api/types';
import type { Locale } from '@/lib/i18n/locale';

interface AreaCatalogProps {
  area: Area;
  projects: Project[];
  locale: Locale;
}

/**
 * Conmutador de capas del catálogo. Es la única pieza que lee la URL, así que es
 * la única que cae dentro del límite de Suspense: la rejilla se prerenderiza
 * fuera y sus tarjetas van en el HTML servido.
 *
 * El estado de las capas vive en la URL (`?subarea=scientist,analyst`), no en
 * memoria: el filtro se comparte, se marca y se navega con el botón atrás. Sin
 * el parámetro, todas las capas están encendidas —que es justo lo que el
 * servidor puede dibujar.
 */
export function AreaCatalog({ area, projects, locale }: AreaCatalogProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { publish } = useLayers();

  const allKeys = useMemo(() => area.subareas.map((subarea) => subarea.key), [area.subareas]);
  const raw = searchParams.get('subarea');

  const active = useMemo(() => {
    if (raw === null) return allKeys;
    return raw
      .split(',')
      .map((key) => key.trim())
      .filter((key) => allKeys.includes(key));
  }, [raw, allKeys]);

  // `null` cuando no hay parámetro: así la rejilla sabe que el estado coincide
  // con el que sirvió el servidor y no tiene que tocar nada.
  const selection = useMemo(() => (raw === null ? null : active), [raw, active]);

  // La primera publicación es la que trae la URL al cargar y se aplica sin
  // animar; de la segunda en adelante vienen de un clic en un chip y sí animan.
  const settled = useRef(false);
  useEffect(() => {
    publish(selection, settled.current);
    settled.current = true;
  }, [selection, publish]);

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
      ).length,
    [projects, active, area.key],
  );

  return (
    <LayerChips
      subareas={area.subareas}
      active={active}
      visible={visible}
      total={projects.length}
      locale={locale}
      onToggle={toggle}
      onReset={() => write(allKeys)}
    />
  );
}

export default AreaCatalog;
