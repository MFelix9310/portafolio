-- Extensiones y utilidades compartidas.
-- gen_random_uuid() vive en pgcrypto (Supabase la instala en el esquema extensions).

create extension if not exists "pgcrypto" with schema extensions;

-- Trigger generico de updated_at. Se adjunta a cada tabla en la migracion
-- correspondiente. search_path fijado para que no dependa del que traiga la sesion.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

comment on function public.set_updated_at() is
  'Trigger BEFORE UPDATE: mantiene updated_at. Ver docs/02-contrato-datos.md.';
