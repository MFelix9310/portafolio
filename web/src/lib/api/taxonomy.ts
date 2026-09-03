import { areaCopyKey, fromCopy } from '../i18n/copy';
import type { AreaKey, Localized } from './types';

/**
 * Taxonomía fija del contrato de datos (D4). Aquí vive sólo la ESTRUCTURA —qué
 * áreas existen, qué subáreas cuelgan de cada una y qué letra rotula la columna—
 * mientras que todo el texto visible sale de `content/copy/*.json`.
 */
export const AREA_ORDER: AreaKey[] = ['data', 'developer', 'civil-bim'];

export const SUBAREAS_BY_AREA: Record<AreaKey, string[]> = {
  data: ['analyst', 'scientist', 'engineer'],
  developer: ['fullstack', 'backend', 'desktop'],
  'civil-bim': ['structural', 'geotechnical', 'bim', 'construction'],
};

/** Rótulo de columna en la retícula: A, B, C. */
const AREA_LABEL: Record<AreaKey, string> = {
  data: 'A',
  developer: 'B',
  'civil-bim': 'C',
};

export function areaLabel(area: AreaKey): string {
  return AREA_LABEL[area];
}

export function areaName(area: AreaKey): Localized {
  const key = areaCopyKey(area);
  return fromCopy((source) => source.microcopy.areas[key]);
}

/** Descripción corta: la que se lee en el índice de áreas de la portada. */
export function areaBlurb(area: AreaKey): Localized {
  const key = areaCopyKey(area);
  return fromCopy((source) => source.home.area_cards[key].description);
}

/** Introducción larga: la cabecera de la página del área. */
export function areaIntro(area: AreaKey): Localized {
  const key = areaCopyKey(area);
  return fromCopy((source) => source.areas[key].intro);
}

export function subareaName(area: AreaKey, subarea: string): Localized {
  const key = areaCopyKey(area);
  return fromCopy((source) => source.microcopy.subareas[key][subarea] ?? subarea);
}

export function isAreaKey(value: string): value is AreaKey {
  return AREA_ORDER.includes(value as AreaKey);
}
