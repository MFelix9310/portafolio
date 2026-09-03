-- admin_users: quien puede escribir. El contrato exige una tabla en vez de un
-- email hardcodeado, para que rotar la cuenta no requiera migracion.

create table public.admin_users (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null unique references auth.users (id) on delete cascade,
  note       text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger admin_users_set_updated_at
  before update on public.admin_users
  for each row execute function public.set_updated_at();

comment on table public.admin_users is
  'Filas cuyo user_id puede escribir. Normalmente una sola (Felix).';

-- is_admin(): unico predicado de escritura de todo el esquema.
--
-- security definer a proposito: la funcion se ejecuta como su propietario, asi
-- que la lectura interna de admin_users NO vuelve a pasar por RLS. Sin esto,
-- cualquier politica de admin_users que llamase a is_admin() recursaria.
-- No se activa `force row level security` en admin_users por la misma razon.
--
-- search_path = '' + nombres cualificados: impide que un search_path hostil
-- resuelva `admin_users` a una tabla plantada por el atacante.
create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.admin_users a
    where a.user_id = (select auth.uid())
  );
$$;

revoke all on function public.is_admin() from public;
grant execute on function public.is_admin() to authenticated, service_role;

comment on function public.is_admin() is
  'true si el JWT actual pertenece a un admin. Usada por todas las politicas de escritura.';

create index admin_users_user_id_idx on public.admin_users (user_id);
