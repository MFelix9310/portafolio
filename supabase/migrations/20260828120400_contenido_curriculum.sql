-- Contenido: experiences, certifications, education, publications, contacts, messages.
--
-- `legacy_id` no aparece en la ficha de estas tablas en docs/02-contrato-datos.md
-- (solo en projects), pero el export de content/catalog.seed.json lo trae para
-- las cuatro. Se anade porque `education` no tiene slug: sin legacy_id no hay
-- ninguna clave estable con la que hacer el seed idempotente.

-- ------------------------------------------------------------- experiences

create table public.experiences (
  id                uuid primary key default gen_random_uuid(),
  slug              text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  company           jsonb not null,
  position          jsonb not null,
  description       jsonb,
  keywords          text[] not null default '{}',
  company_logo_path text,
  thumbnail_path    text,
  start_date        date,
  end_date          date,
  is_current        boolean not null default false,
  legacy_id         int unique,
  status            text not null default 'draft' check (status in ('draft', 'published')),
  display_order     int not null default 0,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  constraint experiences_company_tiene_es check (company ? 'es' and length(company ->> 'es') > 0),
  constraint experiences_rango_fechas check (end_date is null or start_date is null or end_date >= start_date),
  -- Un puesto en curso no puede tener fecha de fin.
  constraint experiences_actual_sin_fin check (not is_current or end_date is null)
);

-- ---------------------------------------------------------- certifications

create table public.certifications (
  id               uuid primary key default gen_random_uuid(),
  slug             text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name             jsonb not null,
  issuer           jsonb,
  description      jsonb,
  issued_on        date,
  expires_on       date,
  credential_url   text,
  certificate_path text,
  legacy_id        int unique,
  status           text not null default 'draft' check (status in ('draft', 'published')),
  display_order    int not null default 0,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  constraint certifications_name_tiene_es check (name ? 'es' and length(name ->> 'es') > 0),
  constraint certifications_rango_fechas check (expires_on is null or issued_on is null or expires_on >= issued_on)
);

-- --------------------------------------------------------------- education

create table public.education (
  id              uuid primary key default gen_random_uuid(),
  institution     jsonb not null,
  title           jsonb not null,
  description     jsonb,
  graduation_year int,
  legacy_id       int unique,
  status          text not null default 'draft' check (status in ('draft', 'published')),
  display_order   int not null default 0,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  constraint education_institution_tiene_es check (institution ? 'es' and length(institution ->> 'es') > 0),
  constraint education_title_tiene_es check (title ? 'es' and length(title ->> 'es') > 0),
  constraint education_ano_plausible check (graduation_year is null or graduation_year between 1900 and 2200)
);

-- ------------------------------------------------------------ publications

create table public.publications (
  id             uuid primary key default gen_random_uuid(),
  slug           text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  -- El contrato no enumera los valores de `kind`, asi que no se restringe aqui.
  kind           text not null,
  title          jsonb not null,
  authors        jsonb,
  venue          jsonb,
  abstract       jsonb,
  published_on   date,
  doi            text,
  isbn           text,
  url            text,
  pdf_path       text,
  thumbnail_path text,
  legacy_id      int unique,
  status         text not null default 'draft' check (status in ('draft', 'published')),
  display_order  int not null default 0,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  constraint publications_title_tiene_es check (title ? 'es' and length(title ->> 'es') > 0)
);

-- ---------------------------------------------------------------- contacts

create table public.contacts (
  id            uuid primary key default gen_random_uuid(),
  kind          text not null,
  value         text not null,
  status        text not null default 'draft' check (status in ('draft', 'published')),
  display_order int not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  -- No hay slug ni legacy_id en el export: (kind, value) es la clave natural
  -- y la que usa el cargador para el upsert.
  constraint contacts_kind_value_unico unique (kind, value)
);

-- ---------------------------------------------------------------- messages
-- Formulario de contacto. Sin `status` ni `display_order`: no es contenido
-- publicable. `anon` inserta y no lee (regla 3 del contrato).

create table public.messages (
  id         uuid primary key default gen_random_uuid(),
  name       text not null check (length(btrim(name)) between 1 and 200),
  email      text not null check (length(email) <= 320 and position('@' in email) > 1),
  subject    text check (length(subject) <= 300),
  body       text not null check (length(btrim(body)) between 1 and 10000),
  read       boolean not null default false,
  created_at timestamptz not null default now()
);

comment on table public.messages is
  'Formulario de contacto. anon puede insert, nunca select. Solo el admin lee.';

-- ----------------------------------------------------------------- triggers

create trigger experiences_set_updated_at
  before update on public.experiences
  for each row execute function public.set_updated_at();

create trigger certifications_set_updated_at
  before update on public.certifications
  for each row execute function public.set_updated_at();

create trigger education_set_updated_at
  before update on public.education
  for each row execute function public.set_updated_at();

create trigger publications_set_updated_at
  before update on public.publications
  for each row execute function public.set_updated_at();

create trigger contacts_set_updated_at
  before update on public.contacts
  for each row execute function public.set_updated_at();
