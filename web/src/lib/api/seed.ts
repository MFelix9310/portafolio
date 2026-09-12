import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import type {
  AreaKey,
  Catalog,
  Localized,
  Project,
  ProjectMedia,
  Rendition,
} from './types';
import {
  AREA_ORDER,
  SUBAREAS_BY_AREA,
  areaBlurb,
  areaIntro,
  areaLabel,
  areaName,
  isAreaKey,
  subareaName,
} from './taxonomy';
import { copy } from '../i18n/copy';
import type { SeedLocalized, SeedProject, SeedRoot } from './seed.types';

/**
 * Fuente de datos de arranque. Sin `NEXT_PUBLIC_API_URL` el front se alimenta del
 * export real del sitio anterior, así que la maqueta se ve con contenido de
 * verdad — y no hace falta levantar FastAPI para trabajar.
 */

/** Una entrada de `content/media-manifest.json`, indexada por ruta heredada. */
interface ManifestEntry {
  kind: 'image' | 'video' | 'document';
  storagePath: string;
  posterPath?: string;
  durationSeconds?: number;
  width?: number;
  height?: number;
  animated?: boolean;
  frames?: number;
  video?: { storagePath: string; bytes: number };
  renditions?: Record<string, { storagePath: string; bytes: number }>;
}

/**
 * Base publica de la media, tambien en modo seed.
 *
 * Estaba fijada a `/media`, que solo existe en local porque `public/media` se
 * puebla con `pnpm media:sync` y no viaja en el repo. En el primer despliegue a
 * Netlify, sin backend, el sitio caia al seed y **todas** las imagenes daban 404.
 *
 * Con `NEXT_PUBLIC_MEDIA_URL` apunta a Supabase Storage; sin ella, a la copia
 * local. En ambos casos la URL es la base mas el `storagePath` completo, que ya
 * incluye el bucket como primer segmento (contrato A4).
 */
const MEDIA_BASE = process.env.NEXT_PUBLIC_MEDIA_URL?.replace(/\/+$/, '') ?? '';

// `slugify` vivía aquí para recomponer a mano las rutas de media. Desde que el
// manifiesto es la fuente de verdad no se usa: las rutas se leen, no se deducen.

function readJson<T>(...candidates: string[]): T | null {
  for (const candidate of candidates) {
    try {
      return JSON.parse(readFileSync(candidate, 'utf8')) as T;
    } catch {
      continue;
    }
  }
  return null;
}

function loadSeed(): SeedRoot {
  const seed = readJson<SeedRoot>(
    join(process.cwd(), '..', 'content', 'catalog.seed.json'),
    join(process.cwd(), 'content', 'catalog.seed.json'),
  );
  if (!seed) throw new Error('No se encontró content/catalog.seed.json');
  return seed;
}

/**
 * `content/media-manifest.json` es la unica fuente de verdad de las rutas de
 * media (contrato A4). Antes se leia el sub-manifiesto de video y se componian
 * las rutas a mano desde la ruta heredada, lo que producia `/media/videos/...`
 * en vez de `/media/projects/videos/...` y servia los originales png en vez de
 * las derivadas webp. Resultado: 21 de 23 assets daban 404.
 */
function loadManifest(): Map<string, ManifestEntry> {
  const manifest = readJson<{ entries?: Record<string, ManifestEntry> }>(
    join(process.cwd(), '..', 'content', 'media-manifest.json'),
    join(process.cwd(), 'content', 'media-manifest.json'),
  );
  return new Map(Object.entries(manifest?.entries ?? {}));
}

/**
 * Manifiesto indexado por `storagePath` en vez de por ruta heredada.
 *
 * Existe para el modo API: el backend emite `storage_path` pero **no** emite el
 * campo `video` de la rendition H.264 de un GIF, asi que sin este indice la
 * galeria en modo API se comeria los 37 MB de WebP animado. Se calcula una sola
 * vez por proceso; el manifiesto viaja con el build (`outputFileTracingIncludes`).
 */
let animatedIndex: Map<string, string> | null = null;

function animatedByStoragePath(): Map<string, string> {
  if (animatedIndex) return animatedIndex;
  animatedIndex = new Map();
  for (const entry of loadManifest().values()) {
    if (!entry.animated || !entry.video?.storagePath) continue;
    animatedIndex.set(entry.storagePath, entry.video.storagePath);
  }
  return animatedIndex;
}

/**
 * Ruta publica del vídeo equivalente a una imagen animada, o `null` si esa
 * imagen no es un GIF. `storagePath` es la ruta del bucket (`media/...`).
 */
export function animatedVideoFor(storagePath: string | null | undefined): string | null {
  if (!storagePath) return null;
  const key = storagePath.replace(/^\/+/, '');
  return assetUrl(animatedByStoragePath().get(key) ?? undefined);
}

function localized(value: SeedLocalized | null | undefined): Localized {
  return { es: value?.es ?? '', en: value?.en ?? null };
}

/**
 * El seed reconstruido desde el sitio en vivo trae los pies de foto y los
 * titulos de documento ya localizados. El seed anterior los traia como cadena
 * plana, asi que se aceptan ambas formas.
 */
function optionalLocalized(
  value: string | SeedLocalized | null | undefined,
): Localized | null {
  if (!value) return null;
  if (typeof value === 'string') return { es: value, en: null };
  return value.es ? { es: value.es, en: value.en ?? null } : null;
}

/** `media/projects/...` incluye el bucket; el front lo sirve bajo `/media/...`. */
function assetUrl(storagePath: string | undefined): string | null {
  // El bucket se conserva: local sirve en `/media/...` y Storage en
  // `.../object/public/media/...`, asi que en los dos casos la ruta es la misma.
  return storagePath ? `${MEDIA_BASE}/${storagePath.replace(/^\/+/, '')}` : null;
}

function toRenditions(entry: ManifestEntry): { '720'?: Rendition; '1080'?: Rendition } {
  const out: { '720'?: Rendition; '1080'?: Rendition } = {};
  for (const label of ['720', '1080'] as const) {
    const rendition = entry.renditions?.[label];
    const src = assetUrl(rendition?.storagePath);
    if (src) out[label] = { src, bytes: rendition?.bytes ?? 0 };
  }
  return out;
}

function buildMedia(project: SeedProject, manifest: Map<string, ManifestEntry>): ProjectMedia[] {
  const media: ProjectMedia[] = [];
  let order = 0;

  for (const video of project.videos ?? []) {
    const entry = manifest.get(video.path);
    if (!entry) continue;
    const renditions = toRenditions(entry);
    const primary = renditions['1080']?.src ?? renditions['720']?.src ?? assetUrl(entry.storagePath);
    if (!primary) continue;
    media.push({
      id: `${project.slug}-video-${order}`,
      kind: 'video',
      src: primary,
      poster: assetUrl(entry.posterPath),
      caption: optionalLocalized(video.caption),
      title: null,
      durationSeconds: entry.durationSeconds ?? null,
      width: entry.width ?? null,
      height: entry.height ?? null,
      renditions,
      displayOrder: order,
    });
    order += 1;
  }

  for (const image of project.images ?? []) {
    const entry = manifest.get(image.path);
    const src = assetUrl(entry?.storagePath);
    if (!src) continue;
    media.push({
      id: `${project.slug}-image-${order}`,
      kind: 'image',
      // Un GIF animado trae ademas una rendition H.264 que pesa un orden de
      // magnitud menos; el consumidor decide cual usa.
      src,
      video: assetUrl(entry?.video?.storagePath),
      poster: null,
      caption: optionalLocalized(image.caption),
      title: null,
      durationSeconds: null,
      width: null,
      height: null,
      renditions: null,
      displayOrder: order,
    });
    order += 1;
  }

  for (const doc of project.documents ?? []) {
    const entry = manifest.get(doc.path);
    const src = assetUrl(entry?.storagePath);
    if (!src) continue;
    media.push({
      id: `${project.slug}-doc-${order}`,
      kind: 'document',
      src,
      poster: null,
      caption: null,
      title: optionalLocalized(doc.title),
      durationSeconds: null,
      width: null,
      height: null,
      renditions: null,
      displayOrder: order,
    });
    order += 1;
  }

  return media;
}

export function buildAreas(projects: Project[]): Catalog['areas'] {
  return AREA_ORDER.map((key) => {
    const inArea = projects.filter((project) => project.tags.some((tag) => tag.area === key));
    return {
      key,
      label: areaLabel(key),
      name: areaName(key),
      blurb: areaBlurb(key),
      intro: areaIntro(key),
      count: inArea.length,
      subareas: (SUBAREAS_BY_AREA[key] ?? []).map((subKey) => ({
        key: subKey,
        areaKey: key,
        name: subareaName(key, subKey),
        count: inArea.filter((project) =>
          project.tags.some((tag) => tag.area === key && tag.subarea === subKey),
        ).length,
      })),
    };
  });
}

/**
 * Los resúmenes del seed son los del sitio Django. El copy los reescribe hecho
 * por hecho, así que manda el copy y el seed queda de red de seguridad para un
 * slug que todavía no esté reescrito.
 */
function summaryOf(slug: string, seedSummary: Localized): Localized {
  const es = copy('es').projects[slug]?.summary;
  const en = copy('en').projects[slug]?.summary;
  if (!es) return seedSummary;
  return { es, en: en ?? null };
}

export function loadCatalogFromSeed(): Catalog {
  const seed = loadSeed();
  const manifest = loadManifest();

  const projects: Project[] = (seed.projects ?? [])
    .filter((project) => project.status === 'published')
    .map((project) => ({
      slug: project.slug,
      title: localized(project.title),
      summary: summaryOf(project.slug, localized(project.summary)),
      body: null,
      technologies: project.technologies ?? [],
      projectUrl: project.project_url,
      repositoryUrl: project.repository_url,
      // Por el manifiesto, no por la ruta heredada: el fichero servido es la
      // derivada webp y su nombre esta normalizado a minusculas sin acentos.
      thumbnail: assetUrl(manifest.get(project.thumbnail ?? '')?.storagePath),
      thumbnailVideo: animatedVideoFor(manifest.get(project.thumbnail ?? '')?.storagePath),
      tags: (project.taxonomy ?? [])
        .filter((tag): tag is { area: AreaKey; subarea: string } => isAreaKey(tag.area))
        .map((tag) => ({ area: tag.area, subarea: tag.subarea })),
      media: buildMedia(project, manifest),
      displayOrder: project.display_order ?? 0,
    }))
    .sort((a, b) => a.displayOrder - b.displayOrder);

  return {
    profile: {
      name: seed.profile.name,
      headline: localized(seed.profile.legacy_title),
      bio: localized(seed.profile.bio),
      photo: assetUrl(manifest.get(seed.profile.professional_photo ?? '')?.storagePath),
    },
    areas: buildAreas(projects),
    projects,
    experiences: (seed.experiences ?? [])
      .filter((item) => item.status === 'published')
      .map((item) => ({
        slug: item.slug,
        company: localized(item.company),
        position: localized(item.position),
        description: localized(item.description),
        keywords: item.keywords ?? [],
        startDate: item.start_date,
        endDate: item.end_date,
        isCurrent: Boolean(item.is_current),
      })),
    certifications: (seed.certifications ?? [])
      .filter((item) => item.status === 'published')
      .map((item) => ({
        slug: item.slug,
        name: localized(item.name),
        issuer: localized(item.issuer),
        description: item.description ? localized(item.description) : null,
        issuedOn: item.issued_on,
        credentialUrl: item.credential_url,
      })),
    education: (seed.education ?? [])
      .filter((item) => item.status === 'published')
      .map((item) => ({
        institution: localized(item.institution),
        title: localized(item.title),
        description: item.description ? localized(item.description) : null,
        graduationYear: item.graduation_year,
      })),
    publications: (seed.publications ?? [])
      .filter((item) => item.status === 'published')
      .map((item) => ({
        slug: item.slug,
        kind: item.kind,
        title: localized(item.title),
        authors: item.authors ? localized(item.authors) : null,
        venue: item.venue ? localized(item.venue) : null,
        abstract: item.abstract ? localized(item.abstract) : null,
        publishedOn: item.published_on,
        url: item.url,
      })),
    contacts: (seed.contacts ?? [])
      .filter((contact) => contact.status === 'published')
      .map((contact) => ({ kind: contact.kind, value: contact.value })),
    source: 'seed',
  };
}
