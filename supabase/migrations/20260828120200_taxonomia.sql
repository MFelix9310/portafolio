-- Taxonomia: areas y subareas. Las tres areas y sus subareas son semilla fija
-- (docs/02-contrato-datos.md) porque las rutas /data, /developer y /civil-bim
-- deben existir aunque tengan cero proyectos. El panel puede anadir mas sin migrar.

create table public.areas (
  id            uuid primary key default gen_random_uuid(),
  key           text not null unique check (key ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name          jsonb not null,
  blurb         jsonb,
  display_order int not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  -- `es` obligatorio, `en` opcional con fallback en el consumidor (D5).
  constraint areas_name_tiene_es check (name ? 'es' and length(name ->> 'es') > 0)
);

create table public.subareas (
  id            uuid primary key default gen_random_uuid(),
  area_id       uuid not null references public.areas (id) on delete cascade,
  key           text not null check (key ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name          jsonb not null,
  display_order int not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  constraint subareas_key_unica_por_area unique (area_id, key),
  constraint subareas_name_tiene_es check (name ? 'es' and length(name ->> 'es') > 0)
);

create trigger areas_set_updated_at
  before update on public.areas
  for each row execute function public.set_updated_at();

create trigger subareas_set_updated_at
  before update on public.subareas
  for each row execute function public.set_updated_at();

create index areas_display_order_idx on public.areas (display_order);
create index subareas_area_id_idx on public.subareas (area_id);
create index subareas_display_order_idx on public.subareas (area_id, display_order);

-- Semilla fija de la taxonomia. Idempotente: si ya existe, actualiza el nombre.
insert into public.areas (key, name, blurb, display_order) values
  ('data',      '{"es": "Datos",       "en": "Data"}',                null, 1),
  ('developer', '{"es": "Desarrollo",  "en": "Development"}',         null, 2),
  ('civil-bim', '{"es": "Civil / BIM", "en": "Civil / BIM"}',         null, 3)
on conflict (key) do update
  set name = excluded.name,
      display_order = excluded.display_order;

insert into public.subareas (area_id, key, name, display_order)
select a.id, s.key, s.name, s.display_order
from (values
  ('data',      'analyst',      '{"es": "Data Analyst",   "en": "Data Analyst"}'::jsonb,    1),
  ('data',      'scientist',    '{"es": "Data Scientist", "en": "Data Scientist"}'::jsonb,  2),
  ('data',      'engineer',     '{"es": "Data Engineer",  "en": "Data Engineer"}'::jsonb,   3),
  ('developer', 'fullstack',    '{"es": "Full Stack",     "en": "Full Stack"}'::jsonb,      1),
  ('developer', 'backend',      '{"es": "Backend",        "en": "Backend"}'::jsonb,         2),
  ('developer', 'desktop',      '{"es": "Escritorio",     "en": "Desktop"}'::jsonb,         3),
  ('civil-bim', 'structural',   '{"es": "Estructuras",    "en": "Structural"}'::jsonb,      1),
  ('civil-bim', 'geotechnical', '{"es": "Geotecnia",      "en": "Geotechnical"}'::jsonb,    2),
  ('civil-bim', 'bim',          '{"es": "BIM",            "en": "BIM"}'::jsonb,             3),
  ('civil-bim', 'construction', '{"es": "Obra",           "en": "Construction"}'::jsonb,    4)
) as s(area_key, key, name, display_order)
join public.areas a on a.key = s.area_key
on conflict (area_id, key) do update
  set name = excluded.name,
      display_order = excluded.display_order;
