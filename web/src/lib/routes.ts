import type { Locale } from './i18n/locale';

/**
 * ES ocupa la raíz (idioma por defecto) y EN cuelga de `/en`. Los segmentos se
 * traducen, así que la tabla vive aquí y nadie concatena rutas a mano.
 */
const SEGMENTS = {
  home: { es: '/', en: '/en' },
  data: { es: '/data', en: '/en/data' },
  developer: { es: '/developer', en: '/en/developer' },
  'civil-bim': { es: '/civil-bim', en: '/en/civil-bim' },
  about: { es: '/sobre-mi', en: '/en/about' },
  contact: { es: '/contacto', en: '/en/contact' },
} as const;

export type RouteKey = keyof typeof SEGMENTS;

export function route(key: RouteKey, locale: Locale): string {
  return SEGMENTS[key][locale];
}

export function projectRoute(slug: string, locale: Locale): string {
  return locale === 'es' ? `/proyectos/${slug}` : `/en/projects/${slug}`;
}

/** Misma página, el otro idioma — para el conmutador del encabezado. */
export function swapLocale(pathname: string, target: Locale): string {
  const clean = pathname.replace(/^\/en(?=\/|$)/, '') || '/';
  const translated = (Object.keys(SEGMENTS) as RouteKey[]).find(
    (key) => SEGMENTS[key].es === clean,
  );
  if (translated) return SEGMENTS[translated][target];
  if (clean.startsWith('/proyectos/')) {
    const slug = clean.slice('/proyectos/'.length);
    return projectRoute(slug, target);
  }
  return target === 'es' ? clean : `/en${clean === '/' ? '' : clean}`;
}
