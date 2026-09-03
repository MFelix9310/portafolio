/**
 * Registro de recursos: una sola fuente para navegación, tablas y formularios.
 *
 * Lo que la API no permite tampoco se pinta. `areas` es el caso claro (A10): la API
 * responde 405 a `POST` y `DELETE`, así que aquí `canCreate` y `canDelete` son
 * falsos y el panel no ofrece esos botones.
 */

import {
  AREA_OPTIONS,
  COMMON_TAIL,
  CONTACT_KIND_OPTIONS,
  PUBLICATION_KIND_OPTIONS,
  STATUS_OPTIONS,
  type ColumnDef,
  type FieldDef,
} from './fields';

export const RESOURCE_KEYS = [
  'projects',
  'experiences',
  'certifications',
  'education',
  'publications',
  'contacts',
  'subareas',
  'areas',
] as const;

export type ResourceKey = (typeof RESOURCE_KEYS)[number];

export interface ResourceDef {
  key: ResourceKey;
  label: string;
  singular: string;
  /** Rótulo del botón de alta: el género del sustantivo no lo sabe una plantilla. */
  newLabel: string;
  columns: ColumnDef[];
  fields: FieldDef[];
  /** Rótulo de una fila; se usa en encabezados y en la confirmación de borrado. */
  titleOf: (row: Record<string, unknown>) => string;
  canCreate: boolean;
  canDelete: boolean;
  canReorder: boolean;
  hasStatus: boolean;
  /** Crear y editar usan verbos distintos según el recurso. */
  updateMethod: 'PATCH' | 'POST';
  note?: string;
}

const es = (value: unknown): string => {
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object' && 'es' in value) {
    return String((value as { es?: string }).es ?? '');
  }
  return '';
};

export const RESOURCES: Record<ResourceKey, ResourceDef> = {
  projects: {
    key: 'projects',
    label: 'Proyectos',
    singular: 'proyecto',
    newLabel: 'Nuevo proyecto',
    canCreate: true,
    canDelete: true,
    canReorder: true,
    hasStatus: true,
    updateMethod: 'PATCH',
    titleOf: (row) => es(row.title) || es(row.slug),
    columns: [
      { key: 'title', label: 'Título', kind: 'localized' },
      { key: 'slug', label: 'Slug', kind: 'text', width: 'w-56' },
      { key: 'technologies', label: 'Tecnologías', kind: 'list', width: 'w-64' },
      { key: 'status', label: 'Estado', kind: 'status', width: 'w-32' },
    ],
    fields: [
      { name: 'slug', label: 'Slug', kind: 'slug', required: true, help: 'Minúsculas ASCII con guiones. Es la URL pública.' },
      { name: 'title', label: 'Título', kind: 'localized', required: true },
      { name: 'summary', label: 'Resumen', kind: 'localized-long', rows: 4 },
      { name: 'body', label: 'Cuerpo', kind: 'localized-long', rows: 12 },
      { name: 'taxonomy', label: 'Área y subárea', kind: 'taxonomy' },
      { name: 'technologies', label: 'Tecnologías', kind: 'list', help: 'Una por línea o separadas por comas.' },
      { name: 'thumbnail_path', label: 'Miniatura', kind: 'path', accept: 'image' },
      { name: 'project_url', label: 'URL del proyecto', kind: 'text' },
      { name: 'repository_url', label: 'Repositorio', kind: 'text' },
      ...COMMON_TAIL,
    ],
  },

  experiences: {
    key: 'experiences',
    label: 'Experiencia',
    singular: 'experiencia',
    newLabel: 'Nueva experiencia',
    canCreate: true,
    canDelete: true,
    canReorder: true,
    hasStatus: true,
    updateMethod: 'PATCH',
    titleOf: (row) => `${es(row.position)} · ${es(row.company)}`.replace(/^ · | · $/, ''),
    columns: [
      { key: 'position', label: 'Puesto', kind: 'localized' },
      { key: 'company', label: 'Empresa', kind: 'localized' },
      { key: 'start_date', label: 'Desde', kind: 'date', width: 'w-28' },
      { key: 'end_date', label: 'Hasta', kind: 'date', width: 'w-28' },
      { key: 'status', label: 'Estado', kind: 'status', width: 'w-32' },
    ],
    fields: [
      { name: 'slug', label: 'Slug', kind: 'slug', required: true },
      { name: 'company', label: 'Empresa', kind: 'localized', required: true },
      { name: 'position', label: 'Puesto', kind: 'localized', required: true },
      { name: 'description', label: 'Descripción', kind: 'localized-long', rows: 8 },
      { name: 'keywords', label: 'Palabras clave', kind: 'list' },
      { name: 'start_date', label: 'Fecha de inicio', kind: 'date', required: true },
      { name: 'end_date', label: 'Fecha de fin', kind: 'date', help: 'Vacío si sigue en curso.' },
      { name: 'is_current', label: 'Puesto actual', kind: 'boolean' },
      { name: 'company_logo_path', label: 'Logotipo', kind: 'path', accept: 'image' },
      { name: 'thumbnail_path', label: 'Miniatura', kind: 'path', accept: 'image' },
      ...COMMON_TAIL,
    ],
  },

  certifications: {
    key: 'certifications',
    label: 'Certificaciones',
    singular: 'certificación',
    newLabel: 'Nueva certificación',
    canCreate: true,
    canDelete: true,
    canReorder: true,
    hasStatus: true,
    updateMethod: 'PATCH',
    titleOf: (row) => es(row.name) || es(row.slug),
    columns: [
      { key: 'name', label: 'Nombre', kind: 'localized' },
      { key: 'issuer', label: 'Emisor', kind: 'localized', width: 'w-56' },
      { key: 'issued_on', label: 'Emitida', kind: 'date', width: 'w-28' },
      { key: 'status', label: 'Estado', kind: 'status', width: 'w-32' },
    ],
    fields: [
      { name: 'slug', label: 'Slug', kind: 'slug', required: true },
      { name: 'name', label: 'Nombre', kind: 'localized', required: true },
      { name: 'issuer', label: 'Emisor', kind: 'localized', required: true },
      { name: 'description', label: 'Descripción', kind: 'localized-long', rows: 6 },
      { name: 'issued_on', label: 'Fecha de emisión', kind: 'date', required: true },
      { name: 'expires_on', label: 'Caduca el', kind: 'date' },
      { name: 'credential_url', label: 'URL de la credencial', kind: 'text' },
      { name: 'certificate_path', label: 'Certificado', kind: 'path', accept: 'document' },
      ...COMMON_TAIL,
    ],
  },

  education: {
    key: 'education',
    label: 'Formación',
    singular: 'titulación',
    newLabel: 'Nueva titulación',
    canCreate: true,
    canDelete: true,
    canReorder: true,
    hasStatus: true,
    updateMethod: 'PATCH',
    titleOf: (row) => es(row.title) || es(row.institution),
    columns: [
      { key: 'title', label: 'Titulación', kind: 'localized' },
      { key: 'institution', label: 'Institución', kind: 'localized' },
      { key: 'graduation_year', label: 'Año', kind: 'number', width: 'w-24' },
      { key: 'status', label: 'Estado', kind: 'status', width: 'w-32' },
    ],
    fields: [
      { name: 'institution', label: 'Institución', kind: 'localized', required: true },
      { name: 'title', label: 'Titulación', kind: 'localized', required: true },
      { name: 'description', label: 'Descripción', kind: 'localized-long', rows: 6 },
      { name: 'graduation_year', label: 'Año de graduación', kind: 'number', nullable: true },
      ...COMMON_TAIL,
    ],
  },

  publications: {
    key: 'publications',
    label: 'Publicaciones',
    singular: 'publicación',
    newLabel: 'Nueva publicación',
    canCreate: true,
    canDelete: true,
    canReorder: true,
    hasStatus: true,
    updateMethod: 'PATCH',
    titleOf: (row) => es(row.title) || es(row.slug),
    columns: [
      { key: 'title', label: 'Título', kind: 'localized' },
      { key: 'kind', label: 'Tipo', kind: 'text', width: 'w-28' },
      { key: 'published_on', label: 'Fecha', kind: 'date', width: 'w-28' },
      { key: 'status', label: 'Estado', kind: 'status', width: 'w-32' },
    ],
    fields: [
      { name: 'slug', label: 'Slug', kind: 'slug', required: true },
      { name: 'kind', label: 'Tipo', kind: 'select', options: PUBLICATION_KIND_OPTIONS },
      { name: 'title', label: 'Título', kind: 'localized', required: true },
      { name: 'authors', label: 'Autores', kind: 'localized' },
      { name: 'venue', label: 'Publicado en', kind: 'localized' },
      { name: 'abstract', label: 'Resumen', kind: 'localized-long', rows: 8 },
      { name: 'published_on', label: 'Fecha de publicación', kind: 'date' },
      { name: 'doi', label: 'DOI', kind: 'text' },
      { name: 'isbn', label: 'ISBN', kind: 'text' },
      { name: 'url', label: 'URL', kind: 'text' },
      { name: 'pdf_path', label: 'PDF', kind: 'path', accept: 'document' },
      { name: 'thumbnail_path', label: 'Miniatura', kind: 'path', accept: 'image' },
      ...COMMON_TAIL,
    ],
  },

  contacts: {
    key: 'contacts',
    label: 'Contactos',
    singular: 'contacto',
    newLabel: 'Nuevo contacto',
    canCreate: true,
    canDelete: true,
    canReorder: true,
    hasStatus: true,
    updateMethod: 'PATCH',
    titleOf: (row) => `${String(row.kind ?? '')}: ${String(row.value ?? '')}`,
    columns: [
      { key: 'kind', label: 'Tipo', kind: 'text', width: 'w-40' },
      { key: 'value', label: 'Valor', kind: 'text' },
      { key: 'status', label: 'Estado', kind: 'status', width: 'w-32' },
    ],
    fields: [
      { name: 'kind', label: 'Tipo', kind: 'select', required: true, options: CONTACT_KIND_OPTIONS },
      { name: 'value', label: 'Valor', kind: 'text', required: true },
      ...COMMON_TAIL,
    ],
    note: 'La pareja (tipo, valor) es única: repetirla devuelve un 409 del backend.',
  },

  subareas: {
    key: 'subareas',
    label: 'Subáreas',
    singular: 'subárea',
    newLabel: 'Nueva subárea',
    canCreate: true,
    canDelete: true,
    canReorder: false,
    hasStatus: false,
    updateMethod: 'POST',
    titleOf: (row) => `${es(row.name)} (${String(row.area ?? '')}/${String(row.key ?? '')})`,
    columns: [
      { key: 'area', label: 'Área', kind: 'text', width: 'w-40' },
      { key: 'key', label: 'Clave', kind: 'text', width: 'w-40' },
      { key: 'name', label: 'Nombre', kind: 'localized' },
      { key: 'display_order', label: 'Orden', kind: 'number', width: 'w-20' },
    ],
    fields: [
      { name: 'area', label: 'Área', kind: 'select', required: true, options: AREA_OPTIONS },
      { name: 'key', label: 'Clave', kind: 'slug', required: true, help: 'Única dentro del área.' },
      { name: 'name', label: 'Nombre', kind: 'localized', required: true },
      { name: 'display_order', label: 'Orden', kind: 'number' },
    ],
  },

  areas: {
    key: 'areas',
    label: 'Áreas',
    singular: 'área',
    newLabel: 'Nueva área',
    // A10: las tres áreas son rutas del App Router. La API responde 405 a POST y
    // DELETE, así que el panel no ofrece lo que la API va a rechazar.
    canCreate: false,
    canDelete: false,
    canReorder: false,
    hasStatus: true,
    updateMethod: 'PATCH',
    titleOf: (row) => es(row.name) || String(row.key ?? ''),
    columns: [
      { key: 'key', label: 'Clave', kind: 'text', width: 'w-40' },
      { key: 'name', label: 'Nombre', kind: 'localized' },
      { key: 'project_count', label: 'Proyectos', kind: 'number', width: 'w-24' },
      { key: 'status', label: 'Estado', kind: 'status', width: 'w-32' },
    ],
    fields: [
      { name: 'name', label: 'Nombre', kind: 'localized', required: true },
      { name: 'blurb', label: 'Descripción corta', kind: 'localized-long', rows: 4 },
      { name: 'status', label: 'Estado', kind: 'select', options: STATUS_OPTIONS },
      { name: 'display_order', label: 'Orden', kind: 'number' },
    ],
    note: 'Las áreas son fijas: /data, /developer y /civil-bim son rutas del sitio. Se editan, no se crean ni se borran.',
  },
};

export function isResourceKey(value: string): value is ResourceKey {
  return (RESOURCE_KEYS as readonly string[]).includes(value);
}
