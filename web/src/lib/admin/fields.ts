/** Vocabulario de campos y columnas. Los formularios y las tablas se generan de aquí. */

export type FieldKind =
  | 'text'
  | 'slug'
  | 'localized'
  | 'localized-long'
  | 'list'
  | 'number'
  | 'date'
  | 'boolean'
  | 'select'
  | 'path'
  | 'taxonomy';

export interface FieldDef {
  name: string;
  label: string;
  kind: FieldKind;
  /** Solo se exige el ES. El EN nunca bloquea la publicación (D5). */
  required?: boolean;
  /** Numérico que la API acepta como `null`. Sin esto, vacío se omite del cuerpo. */
  nullable?: boolean;
  help?: string;
  placeholder?: string;
  options?: readonly { value: string; label: string }[];
  rows?: number;
  accept?: 'image' | 'video' | 'document';
}

export type ColumnKind = 'localized' | 'text' | 'date' | 'status' | 'list' | 'boolean' | 'number';

export interface ColumnDef {
  key: string;
  label: string;
  kind: ColumnKind;
  /** Clase de anchura de Tailwind; sin ella la columna se reparte lo que quede. */
  width?: string;
}

export const STATUS_OPTIONS = [
  { value: 'draft', label: 'Borrador' },
  { value: 'published', label: 'Publicado' },
] as const;

export const AREA_OPTIONS = [
  { value: 'data', label: 'Data' },
  { value: 'developer', label: 'Developer' },
  { value: 'civil-bim', label: 'Civil / BIM' },
] as const;

export const PUBLICATION_KIND_OPTIONS = [
  { value: 'article', label: 'Artículo' },
  { value: 'book', label: 'Libro' },
  { value: 'chapter', label: 'Capítulo' },
  { value: 'thesis', label: 'Tesis' },
  { value: 'report', label: 'Informe' },
] as const;

export const CONTACT_KIND_OPTIONS = [
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Teléfono' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'github', label: 'GitHub' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'website', label: 'Web' },
] as const;

export const MEDIA_KIND_OPTIONS = [
  { value: 'image', label: 'Imagen' },
  { value: 'video', label: 'Vídeo' },
  { value: 'document', label: 'Documento' },
] as const;

const ORDER_FIELD: FieldDef = {
  name: 'display_order',
  label: 'Orden',
  kind: 'number',
  help: 'Menor primero. También se puede cambiar desde el listado.',
};

const STATUS_FIELD: FieldDef = {
  name: 'status',
  label: 'Estado',
  kind: 'select',
  options: STATUS_OPTIONS,
};

export const COMMON_TAIL: readonly FieldDef[] = [STATUS_FIELD, ORDER_FIELD];
