/**
 * Formas que devuelven los presentadores de FastAPI (`schemas/presenters.py`).
 *
 * Son distintas de las de `lib/api/types.ts`: aquel es el modelo ya masajeado para
 * el sitio público (un idioma resuelto, nombres en camelCase); aquí llega la fila
 * canónica con los dos idiomas y snake_case, que es lo que el panel edita y lo que
 * `PATCH /admin/{recurso}/{id}` espera de vuelta.
 */

import type { AreaKey, Localized, MediaKind } from '../api/types';

export type { AreaKey, Localized, MediaKind };

export type Status = 'draft' | 'published';

export interface AdminMedia {
  id: string | null;
  project_id: string | null;
  kind: MediaKind;
  storage_path: string;
  storage_url: string | null;
  poster_path: string | null;
  poster_url: string | null;
  caption: Localized | null;
  title: Localized | null;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  renditions: Record<string, { path: string; url: string | null; bytes: number }>;
  display_order: number;
}

export interface AdminProject {
  id: string | null;
  slug: string;
  title: Localized;
  summary: Localized | null;
  body: Localized | null;
  technologies: string[];
  project_url: string | null;
  repository_url: string | null;
  thumbnail_path: string | null;
  thumbnail_url: string | null;
  legacy_id: number | null;
  status: Status;
  display_order: number;
  taxonomy: { area: AreaKey; subarea: string }[];
  media: AdminMedia[];
}

export interface AdminExperience {
  id: string | null;
  slug: string;
  company: Localized;
  position: Localized;
  description: Localized | null;
  keywords: string[];
  company_logo_path: string | null;
  thumbnail_path: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  legacy_id: number | null;
  status: Status;
  display_order: number;
}

export interface AdminCertification {
  id: string | null;
  slug: string;
  name: Localized;
  issuer: Localized;
  description: Localized | null;
  issued_on: string;
  expires_on: string | null;
  credential_url: string | null;
  certificate_path: string | null;
  legacy_id: number | null;
  status: Status;
  display_order: number;
}

export interface AdminEducation {
  id: string | null;
  institution: Localized;
  title: Localized;
  description: Localized | null;
  graduation_year: number | null;
  legacy_id: number | null;
  status: Status;
  display_order: number;
}

export interface AdminPublication {
  id: string | null;
  slug: string;
  kind: string;
  title: Localized;
  authors: Localized | null;
  venue: Localized | null;
  abstract: Localized | null;
  published_on: string | null;
  doi: string | null;
  isbn: string | null;
  url: string | null;
  pdf_path: string | null;
  thumbnail_path: string | null;
  legacy_id: number | null;
  status: Status;
  display_order: number;
}

export interface AdminContact {
  id: string | null;
  kind: string;
  value: string;
  status: Status;
  display_order: number;
}

export interface AdminProfile {
  id: string | null;
  name: string;
  headline: Localized;
  bio: Localized;
  photo_path: string | null;
  photo_url: string | null;
  professional_photo_path: string | null;
  professional_photo_url: string | null;
  status: Status;
}

export interface AdminSubarea {
  id: string | null;
  area: AreaKey;
  key: string;
  name: Localized;
  display_order: number;
}

export interface AdminArea {
  /** Puede faltar: `presenters.area_overview` aún no lo emite (ver informe). */
  id?: string | null;
  key: AreaKey;
  name: Localized;
  blurb: Localized | null;
  display_order: number;
  status: Status;
  project_count: number;
  subareas: { key: string; name: Localized; display_order: number; project_count: number }[];
}

export interface AdminMessage {
  id: string | null;
  name: string;
  email: string;
  subject: string | null;
  body: string;
  read: boolean;
  created_at: string;
}

export interface UploadTicket {
  upload_url: string;
  storage_path: string;
  public_url: string;
  expires_at: string;
  token: string | null;
}

/** Fila mínima común a todo listado: es lo que la tabla genérica necesita. */
export interface AdminRow {
  id: string | null;
  status?: Status;
  display_order: number;
  [key: string]: unknown;
}
