/**
 * Forma cruda del export heredado (`content/catalog.seed.json`). Vive separada
 * del normalizador para que `seed.ts` hable sólo de la traducción al dominio.
 */

export interface SeedLocalized {
  es: string;
  en?: string | null;
}

export interface SeedMediaRef {
  path: string;
  caption?: string | null;
  title?: string | null;
  order?: number;
}

export interface SeedProject {
  slug: string;
  title: SeedLocalized;
  summary: SeedLocalized;
  technologies: string[];
  project_url: string | null;
  repository_url: string | null;
  thumbnail: string | null;
  display_order: number;
  status: string;
  taxonomy: { area: string; subarea: string }[];
  images: SeedMediaRef[];
  videos: SeedMediaRef[];
  documents: SeedMediaRef[];
}

export interface SeedExperience {
  slug: string;
  company: SeedLocalized;
  position: SeedLocalized;
  description: SeedLocalized;
  keywords: string[];
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  status: string;
}

export interface SeedCertification {
  slug: string;
  name: SeedLocalized;
  issuer: SeedLocalized;
  description: SeedLocalized | null;
  issued_on: string | null;
  credential_url: string | null;
  status: string;
}

export interface SeedEducation {
  institution: SeedLocalized;
  title: SeedLocalized;
  description: SeedLocalized | null;
  graduation_year: number | null;
  status: string;
}

export interface SeedPublication {
  slug: string;
  kind: string;
  title: SeedLocalized;
  authors: SeedLocalized | null;
  venue: SeedLocalized | null;
  abstract: SeedLocalized | null;
  published_on: string | null;
  url: string | null;
  status: string;
}

export interface SeedRoot {
  profile: {
    name: string;
    legacy_title: SeedLocalized;
    bio: SeedLocalized;
    photo: string | null;
    professional_photo: string | null;
  };
  projects: SeedProject[];
  experiences: SeedExperience[];
  certifications: SeedCertification[];
  education: SeedEducation[];
  publications: SeedPublication[];
  contacts: { kind: string; value: string; status: string }[];
}
