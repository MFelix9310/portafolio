/**
 * Traducción entre la fila de la API y los valores del formulario, y validación.
 *
 * Se importa desde el cliente (validación al escribir) y desde las acciones de
 * servidor (validación antes de llamar a la API). La del servidor es la que cuenta,
 * y por debajo el backend valida otra vez: son tres cercos, no uno.
 */

import type { FieldDef } from './fields';

/** Cualquier cosa con campos sirve: el perfil no es un recurso del registro. */
export interface FieldSet {
  fields: readonly FieldDef[];
}


export interface LocalizedValue {
  es: string;
  en: string;
}

export type FormValue = string | number | boolean | null | LocalizedValue | string[] | TaxonomyValue[];
export type FormValues = Record<string, FormValue>;
export interface TaxonomyValue {
  area: string;
  subarea: string;
}

const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function emptyLocalized(): LocalizedValue {
  return { es: '', en: '' };
}

function readLocalized(raw: unknown): LocalizedValue {
  if (raw && typeof raw === 'object') {
    const value = raw as { es?: unknown; en?: unknown };
    return { es: String(value.es ?? ''), en: String(value.en ?? '') };
  }
  return emptyLocalized();
}

export function defaultValue(field: FieldDef): FormValue {
  switch (field.kind) {
    case 'localized':
    case 'localized-long':
      return emptyLocalized();
    case 'list':
      return [];
    case 'taxonomy':
      return [];
    case 'boolean':
      return false;
    case 'number':
      return '';
    case 'select':
      return field.options?.[0]?.value ?? '';
    default:
      return '';
  }
}

export function initialValues(def: FieldSet, row?: Record<string, unknown> | null): FormValues {
  const values: FormValues = {};
  for (const field of def.fields) {
    const raw = row?.[field.name];
    if (raw === undefined || raw === null) {
      values[field.name] = defaultValue(field);
      continue;
    }
    switch (field.kind) {
      case 'localized':
      case 'localized-long':
        values[field.name] = readLocalized(raw);
        break;
      case 'list':
        values[field.name] = Array.isArray(raw) ? raw.map(String) : [];
        break;
      case 'taxonomy':
        values[field.name] = Array.isArray(raw)
          ? (raw as TaxonomyValue[]).map((tag) => ({ area: tag.area, subarea: tag.subarea }))
          : [];
        break;
      case 'boolean':
        values[field.name] = Boolean(raw);
        break;
      case 'number':
        values[field.name] = String(raw);
        break;
      default:
        values[field.name] = String(raw);
    }
  }
  return values;
}

function localizedPayload(value: LocalizedValue): { es: string; en?: string } | null {
  const spanish = value.es.trim();
  const english = value.en.trim();
  if (!spanish) return null;
  // El EN es opcional por contrato (D5): si falta, se omite la clave en vez de
  // mandar cadena vacía, que el dominio rechazaría.
  return english ? { es: spanish, en: english } : { es: spanish };
}

/** Cuerpo JSON para `POST`/`PATCH`. Vacío significa `null`, no cadena vacía. */
export function toPayload(def: FieldSet, values: FormValues): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  for (const field of def.fields) {
    const raw = values[field.name];
    switch (field.kind) {
      case 'localized':
      case 'localized-long':
        payload[field.name] = localizedPayload(raw as LocalizedValue);
        break;
      case 'list':
        payload[field.name] = (raw as string[]).map((item) => item.trim()).filter(Boolean);
        break;
      case 'taxonomy':
        payload[field.name] = (raw as TaxonomyValue[]).filter((tag) => tag.area && tag.subarea);
        break;
      case 'boolean':
        payload[field.name] = Boolean(raw);
        break;
      case 'number': {
        const text = String(raw ?? '').trim();
        if (text !== '') {
          payload[field.name] = Number(text);
        } else if (field.nullable) {
          payload[field.name] = null;
        }
        // Si no es nullable se omite la clave: `display_order` es `int` con
        // defecto en el backend y un `null` explícito lo hace fallar con 422.
        break;
      }
      default: {
        const text = String(raw ?? '').trim();
        payload[field.name] = text === '' ? null : text;
      }
    }
  }
  return payload;
}

export type FieldErrors = Record<string, string>;

export function validate(def: FieldSet, values: FormValues): FieldErrors {
  const errors: FieldErrors = {};
  for (const field of def.fields) {
    const raw = values[field.name] ?? defaultValue(field);
    const message = validateField(field, raw);
    if (message) errors[field.name] = message;
  }
  return errors;
}

export function validateField(field: FieldDef, raw: FormValue): string | null {
  if (field.kind === 'localized' || field.kind === 'localized-long') {
    const value = raw as LocalizedValue;
    if (field.required && !value.es.trim()) return 'El castellano es obligatorio.';
    return null;
  }

  if (field.kind === 'slug') {
    const text = String(raw ?? '').trim();
    if (!text) return field.required ? 'Obligatorio.' : null;
    if (!SLUG_RE.test(text)) return 'Minúsculas ASCII, dígitos y guiones simples.';
    if (text.length > 120) return 'Máximo 120 caracteres.';
    return null;
  }

  if (field.kind === 'date') {
    const text = String(raw ?? '').trim();
    if (!text) return field.required ? 'Obligatorio.' : null;
    if (!DATE_RE.test(text)) return 'Formato AAAA-MM-DD.';
    return null;
  }

  if (field.kind === 'number') {
    const text = String(raw ?? '').trim();
    if (!text) return field.required ? 'Obligatorio.' : null;
    if (!Number.isFinite(Number(text))) return 'Debe ser un número.';
    return null;
  }

  if (field.kind === 'text' || field.kind === 'select' || field.kind === 'path') {
    const text = String(raw ?? '').trim();
    if (field.required && !text) return 'Obligatorio.';
    return null;
  }

  return null;
}

/** Igualdad estructural barata: basta para saber si hay cambios sin guardar. */
export function isDirty(a: FormValues, b: FormValues): boolean {
  return JSON.stringify(a) !== JSON.stringify(b);
}
