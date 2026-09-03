import esJson from '../../../../content/copy/copy.es.json';
import enJson from '../../../../content/copy/copy.en.json';

import type { Locale } from './locale';

/**
 * `content/copy/*.json` es la ÚNICA fuente de copy del sitio. Este módulo es el
 * cargador tipado: la anotación `const ES: Copy = esJson` hace que el build
 * falle si el JSON pierde una clave, así que el contrato con el agente de
 * contenido lo verifica el compilador, no la revisión manual.
 */

export interface CopyProject {
  summary: string;
}

export interface Copy {
  meta: { language: string; positioning: string };
  nav: {
    home: string;
    about: string;
    projects: string;
    contact: string;
    areas: { data: string; developer: string; civil_bim: string };
  };
  home: {
    headline: string;
    subtitle: string;
    intro: string;
    cta_view_projects: string;
    area_cards: Record<AreaCopyKey, { title: string; description: string }>;
  };
  areas: {
    data: { intro: string };
    developer: { intro: string };
    civil_bim: { intro: string; empty_state: { title: string; body: string } };
  };
  about: { heading: string; paragraphs: string[] };
  contact: {
    heading: string;
    support_text: string;
    form: {
      labels: { name: string; email: string; subject: string; message: string };
      submit: string;
      submitting: string;
      success: string;
      errors: {
        name_required: string;
        email_required: string;
        email_invalid: string;
        subject_required: string;
        message_required: string;
        message_too_short: string;
        generic_error: string;
      };
    };
    channels: Record<string, string>;
  };
  projects: Record<string, CopyProject>;
  microcopy: {
    areas: Record<AreaCopyKey, string>;
    subareas: {
      data: Record<string, string>;
      developer: Record<string, string>;
      civil_bim: Record<string, string>;
    };
    buttons: Record<string, string>;
    empty_states: Record<string, string>;
    footer: { tagline: string; copyright: string };
  };
  chrome: {
    skip_to_content: string;
    eyebrow: string;
    thesis: string;
    measure: string;
    menu: { label: string; open: string; close: string };
    language_label: string;
    theme: { label: string; system: string; light: string; dark: string };
    areas_index: { heading: string; note: string };
    layers: {
      label: string;
      help: string;
      reset: string;
      showing: string;
      of: string;
      projects: string;
      projects_one: string;
      all_off: string;
    };
    metrics: {
      projects: string;
      projects_one: string;
      years_in_data: string;
      areas: string;
      experience: string;
      experience_one: string;
      certifications: string;
      certifications_one: string;
      publications: string;
      publications_one: string;
    };
    sheet: {
      label: string;
      scale: string;
      source: string;
      source_seed: string;
      source_api: string;
    };
    video: {
      close: string;
      duration: string;
      size: string;
      dialog: string;
      unsupported: string;
    };
    project: {
      technologies: string;
      links: string;
      video: string;
      images: string;
      documents: string;
    };
    about: {
      experience: string;
      education: string;
      certifications: string;
      publications: string;
      present: string;
      credential: string;
    };
    contact_channels: string;
    contact_form_offline: string;
    civil_bim: {
      stamp: string;
      note: string;
      meanwhile: string;
      meanwhile_body: string;
      /** Fallback de la planta 2D. No se retira hasta que el gesto 4 confirme que ya no lo usa. */
      placeholder_3d: string;
      /** Rótulo de la planta estructural (gesto 4). */
      extrusion_plan: string;
      /** Rótulo de la escena mientras el scroll conduce la extrusión (gesto 4). */
      extrusion_scene: string;
      /** Descripción larga de la planta, para lectores de pantalla (gesto 4). */
      extrusion_alt: string;
    };
    not_found: { eyebrow: string; title: string; body: string; back: string };
  };
}

/** El copy usa snake_case (`civil_bim`); las rutas y la taxonomía usan `civil-bim`. */
export type AreaCopyKey = 'data' | 'developer' | 'civil_bim';

const ES: Copy = esJson;
const EN: Copy = enJson;

export function copy(locale: Locale): Copy {
  return locale === 'en' ? EN : ES;
}

export function areaCopyKey(area: string): AreaCopyKey {
  return area === 'civil-bim' ? 'civil_bim' : (area as AreaCopyKey);
}

/** Construye un `Localized` a partir de la misma clave en los dos idiomas. */
export function fromCopy(pick: (source: Copy) => string): { es: string; en: string } {
  return { es: pick(ES), en: pick(EN) };
}

/** «1 publicaciones» no es español. Sólo el uno lleva forma singular. */
export function plural(count: number, one: string, many: string): string {
  return count === 1 ? one : many;
}

/** `© {year} Félix Ruiz M.` → resuelto en runtime, no es un dato del catálogo. */
export function withYear(template: string, year: number): string {
  return template.replace('{year}', String(year));
}
