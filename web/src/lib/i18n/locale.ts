export const LOCALES = ['es', 'en'] as const;
export type Locale = (typeof LOCALES)[number];

/** ES es obligatorio en el contrato de datos; EN es opcional (D5). */
export const DEFAULT_LOCALE: Locale = 'es';

export type Localized = { es: string; en?: string | null };

export function isLocale(value: string | undefined): value is Locale {
  return value === 'es' || value === 'en';
}

/** Devuelve el texto en el idioma pedido, con caída a ES si falta la traducción. */
export function t(value: Localized | null | undefined, locale: Locale): string {
  if (!value) return '';
  if (locale === 'en') {
    const en = value.en?.trim();
    if (en) return en;
  }
  return value.es ?? '';
}

/** Prefijo de ruta: ES vive en la raíz, EN cuelga de /en. */
export function localePrefix(locale: Locale): string {
  return locale === 'es' ? '' : '/en';
}
