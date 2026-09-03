import { cache } from 'react';

import { apiGet } from './client';
import { animatedVideoFor, loadCatalogFromSeed } from './seed';
import type { Area, AreaKey, Catalog, Project } from './types';

/**
 * Fachada de datos. Un único punto de entrada para las páginas: intenta la API
 * del contrato y, si no hay backend, sirve el seed. El resto del front no sabe
 * de dónde vienen los datos.
 */

const REMOTE_MEDIA_BASE = process.env.NEXT_PUBLIC_MEDIA_URL?.replace(/\/+$/, '') ?? '';

interface RawLocalized {
  es?: string;
  en?: string | null;
}

interface RawMedia {
  kind?: string;
  storage_path?: string;
  /** Rendition H.264 de una imagen animada. Reservado: la API aun no lo emite. */
  video?: string | null;
  poster_path?: string | null;
  caption?: RawLocalized | null;
  title?: RawLocalized | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  renditions?: Record<string, { path?: string; bytes?: number }> | null;
  display_order?: number;
}

interface RawProject {
  slug: string;
  title?: RawLocalized;
  summary?: RawLocalized;
  body?: RawLocalized | null;
  technologies?: string[];
  project_url?: string | null;
  repository_url?: string | null;
  thumbnail_path?: string | null;
  // Nombre tal como lo emite la API. Cuando aqui ponia `subareas`, el tipo
  // mentia sobre el payload y TypeScript no podia detectar la lectura erronea.
  taxonomy?: { area?: string; subarea?: string }[];
  media?: RawMedia[];
  display_order?: number;
}

interface RawCatalog {
  profile?: {
    name?: string;
    headline?: RawLocalized;
    bio?: RawLocalized;
    professional_photo_path?: string | null;
  };
  projects?: RawProject[];
  experiences?: unknown[];
  certifications?: unknown[];
  education?: unknown[];
  publications?: unknown[];
  contacts?: { kind?: string; value?: string }[];
}

const AREA_KEYS: AreaKey[] = ['data', 'developer', 'civil-bim'];

function asset(path: string | null | undefined): string | null {
  if (!path) return null;
  if (/^https?:\/\//.test(path)) return path;
  return `${REMOTE_MEDIA_BASE}/${path.replace(/^\/+/, '')}`;
}

function loc(value: RawLocalized | null | undefined) {
  return { es: value?.es ?? '', en: value?.en ?? null };
}

function fromApi(raw: RawCatalog): Catalog | null {
  if (!raw?.projects) return null;

  const projects: Project[] = raw.projects.map((project) => ({
    slug: project.slug,
    title: loc(project.title),
    summary: loc(project.summary),
    body: project.body ? loc(project.body) : null,
    technologies: project.technologies ?? [],
    projectUrl: project.project_url ?? null,
    repositoryUrl: project.repository_url ?? null,
    thumbnail: asset(project.thumbnail_path),
    thumbnailVideo: animatedVideoFor(project.thumbnail_path),
    // La API emite `taxonomy`, no `subareas`. Leer la clave equivocada dejaba
    // `tags` vacio y las tres areas mostraban cero proyectos en modo API.
    tags: (project.taxonomy ?? [])
      .filter((tag): tag is { area: AreaKey; subarea: string } =>
        Boolean(tag.area && tag.subarea && AREA_KEYS.includes(tag.area as AreaKey)),
      )
      .map((tag) => ({ area: tag.area, subarea: tag.subarea })),
    media: (project.media ?? []).map((item, index) => {
      const renditions = item.renditions ?? null;
      const build = (label: '720' | '1080') => {
        const entry = renditions?.[label];
        const src = asset(entry?.path);
        return src ? { src, bytes: entry?.bytes ?? 0 } : undefined;
      };
      return {
        id: `${project.slug}-media-${index}`,
        kind: (item.kind ?? 'image') as Project['media'][number]['kind'],
        src: asset(item.storage_path) ?? '',
        // La API todavia no emite `video` (el presentador de media no lo tiene),
        // asi que la rendition H.264 de los GIF se recupera del manifiesto que
        // viaja con el build. En cuanto el backend lo emita, esto pasa a ser
        // `item.video ?? animatedVideoFor(...)` y se puede tirar.
        video: item.video ? asset(item.video) : animatedVideoFor(item.storage_path),
        poster: asset(item.poster_path),
        caption: item.caption ? loc(item.caption) : null,
        title: item.title ? loc(item.title) : null,
        durationSeconds: item.duration_seconds ?? null,
        width: item.width ?? null,
        height: item.height ?? null,
        renditions: renditions ? { '720': build('720'), '1080': build('1080') } : null,
        displayOrder: item.display_order ?? index,
      };
    }),
    displayOrder: project.display_order ?? 0,
  }));

  const seedShaped = loadCatalogFromSeed();
  return {
    ...seedShaped,
    profile: {
      name: raw.profile?.name ?? seedShaped.profile.name,
      headline: loc(raw.profile?.headline),
      bio: loc(raw.profile?.bio),
      photo: asset(raw.profile?.professional_photo_path) ?? seedShaped.profile.photo,
    },
    projects,
    areas: countAreas(seedShaped.areas, projects),
    contacts: (raw.contacts ?? [])
      .filter((contact): contact is { kind: string; value: string } =>
        Boolean(contact.kind && contact.value),
      )
      .map((contact) => ({ kind: contact.kind, value: contact.value })),
    source: 'api',
  };
}

/** Recalcula los conteos de la taxonomía sobre el conjunto de proyectos recibido. */
function countAreas(areas: Area[], projects: Project[]): Area[] {
  return areas.map((area) => {
    const inArea = projects.filter((project) => project.tags.some((tag) => tag.area === area.key));
    return {
      ...area,
      count: inArea.length,
      subareas: area.subareas.map((subarea) => ({
        ...subarea,
        count: inArea.filter((project) =>
          project.tags.some((tag) => tag.area === area.key && tag.subarea === subarea.key),
        ).length,
      })),
    };
  });
}

/** `cache` evita releer el seed una vez por componente dentro de la misma request. */
export const getCatalog = cache(async (): Promise<Catalog> => {
  const remote = await apiGet<RawCatalog>('/catalog');
  if (remote) {
    const mapped = fromApi(remote);
    if (mapped) return mapped;
  }
  return loadCatalogFromSeed();
});

export async function getArea(key: AreaKey): Promise<Area | undefined> {
  const catalog = await getCatalog();
  return catalog.areas.find((area) => area.key === key);
}

export async function getProjectsByArea(key: AreaKey): Promise<Project[]> {
  const catalog = await getCatalog();
  return catalog.projects.filter((project) => project.tags.some((tag) => tag.area === key));
}

export async function getProject(slug: string): Promise<Project | undefined> {
  const catalog = await getCatalog();
  return catalog.projects.find((project) => project.slug === slug);
}

export async function getProjectSlugs(): Promise<string[]> {
  const catalog = await getCatalog();
  return catalog.projects.map((project) => project.slug);
}
