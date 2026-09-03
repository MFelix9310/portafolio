-- Contenido: profile, projects, project_subareas, project_media.
--
-- Convenciones del contrato aplicadas en todas las tablas de esta migracion:
--   id uuid pk, created_at, updated_at (+ trigger), status con check, display_order.
--   Todo texto visible es jsonb {"es": ..., "en": ...} con `es` obligatorio.

-- ---------------------------------------------------------------- profile

create table public.profile (
  id                       uuid primary key default gen_random_uuid(),
  -- Singleton: la constraint unique sobre una columna que solo puede valer true
  -- impide fisicamente una segunda fila.
  singleton                boolean not null default true unique check (singleton),
  name                     text not null,
  headline                 jsonb,
  bio                      jsonb,
  photo_path               text,
  professional_photo_path  text,
  status                   text not null default 'published' check (status in ('draft', 'published')),
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

create trigger profile_set_updated_at
  before update on public.profile
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------- projects

create table public.projects (
  id             uuid primary key default gen_random_uuid(),
  slug           text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  title          jsonb not null,
  summary        jsonb,
  body           jsonb,
  technologies   text[] not null default '{}',
  project_url    text,
  repository_url text,
  thumbnail_path text,
  -- Identificador de la fila equivalente en el sitio Django antiguo.
  -- Es la clave de idempotencia del cargador cuando el slug cambia.
  legacy_id      int unique,
  status         text not null default 'draft' check (status in ('draft', 'published')),
  display_order  int not null default 0,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  constraint projects_title_tiene_es check (title ? 'es' and length(title ->> 'es') > 0)
);

create trigger projects_set_updated_at
  before update on public.projects
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------- project_subareas (N:M)
-- D4: /data, /developer y /civil-bim son vistas filtradas de esta relacion.
-- Un proyecto puede pertenecer a varias areas.

create table public.project_subareas (
  project_id uuid not null references public.projects (id) on delete cascade,
  subarea_id uuid not null references public.subareas (id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (project_id, subarea_id)
);

-- ---------------------------------------------------------- project_media

create table public.project_media (
  id               uuid primary key default gen_random_uuid(),
  project_id       uuid not null references public.projects (id) on delete cascade,
  kind             text not null check (kind in ('image', 'video', 'document')),
  storage_path     text not null,
  poster_path      text,
  caption          jsonb,
  title            jsonb,
  duration_seconds numeric,
  width            int,
  height           int,
  -- Salida de tools/media: {"1080": {"path": "...", "bytes": 3980000}, "720": {...}}
  renditions       jsonb,
  display_order    int not null default 0,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  -- Un mismo fichero no se registra dos veces en el mismo proyecto.
  -- Tambien es la clave de idempotencia del cargador de semilla.
  constraint project_media_path_unico unique (project_id, storage_path),
  constraint project_media_dimensiones_positivas
    check ((width is null or width > 0) and (height is null or height > 0)),
  constraint project_media_duracion_positiva
    check (duration_seconds is null or duration_seconds >= 0)
);

create trigger project_media_set_updated_at
  before update on public.project_media
  for each row execute function public.set_updated_at();
