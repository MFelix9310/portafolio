import type { Localized } from '../i18n/locale';

export type { Localized };

export type AreaKey = 'data' | 'developer' | 'civil-bim';
export type MediaKind = 'image' | 'video' | 'document';

export interface Rendition {
  src: string;
  bytes: number;
}

export interface ProjectMedia {
  id: string;
  kind: MediaKind;
  src: string;
  /**
   * Solo en imagenes animadas. El contenido recuperado del sitio en vivo trae
   * GIF de hasta 334 fotogramas: en WebP animado pesan 37 MB y en H.264 pesan
   * 2 MB. Quien pueda usar un `video` en bucle debe preferir esta ruta.
   */
  video?: string | null;
  poster: string | null;
  caption: Localized | null;
  title: Localized | null;
  durationSeconds: number | null;
  width: number | null;
  height: number | null;
  /** Salida de `tools/media`: 720 para viewports pequeños, 1080 para grandes. */
  renditions: { '720'?: Rendition; '1080'?: Rendition } | null;
  displayOrder: number;
}

export interface ProjectTag {
  area: AreaKey;
  subarea: string;
}

export interface Project {
  slug: string;
  title: Localized;
  summary: Localized;
  body: Localized | null;
  technologies: string[];
  projectUrl: string | null;
  repositoryUrl: string | null;
  thumbnail: string | null;
  /**
   * Rendition H.264 de la miniatura cuando la miniatura es un GIF. Cuatro de las
   * portadas del catálogo son animaciones de 1,6 a 3 MB en WebP: servirlas como
   * vídeo en bucle deja la rejilla del área en una décima parte.
   */
  thumbnailVideo: string | null;
  tags: ProjectTag[];
  media: ProjectMedia[];
  displayOrder: number;
}

export interface Subarea {
  key: string;
  areaKey: AreaKey;
  name: Localized;
  count: number;
}

export interface Area {
  key: AreaKey;
  name: Localized;
  /** Descripción corta, para el índice de la portada. */
  blurb: Localized;
  /** Introducción larga, para la cabecera de la página del área. */
  intro: Localized;
  /** Rótulo de columna en la retícula: A, B, C. */
  label: string;
  subareas: Subarea[];
  count: number;
}

export interface Experience {
  slug: string;
  company: Localized;
  position: Localized;
  description: Localized;
  keywords: string[];
  startDate: string;
  endDate: string | null;
  isCurrent: boolean;
}

export interface Certification {
  slug: string;
  name: Localized;
  issuer: Localized;
  description: Localized | null;
  issuedOn: string | null;
  credentialUrl: string | null;
}

export interface Education {
  institution: Localized;
  title: Localized;
  description: Localized | null;
  graduationYear: number | null;
}

export interface Publication {
  slug: string;
  kind: string;
  title: Localized;
  authors: Localized | null;
  venue: Localized | null;
  abstract: Localized | null;
  publishedOn: string | null;
  url: string | null;
}

export interface Contact {
  kind: string;
  value: string;
}

export interface Profile {
  name: string;
  headline: Localized;
  bio: Localized;
  photo: string | null;
}

export interface Catalog {
  profile: Profile;
  areas: Area[];
  projects: Project[];
  experiences: Experience[];
  certifications: Certification[];
  education: Education[];
  publications: Publication[];
  contacts: Contact[];
  /** De dónde salieron los datos; se rotula en el cajetín del pie. */
  source: 'api' | 'seed';
}
