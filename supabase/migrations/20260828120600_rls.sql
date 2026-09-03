-- RLS: el contrato de seguridad (docs/02-contrato-datos.md, seccion RLS).
--
-- Cuatro reglas:
--   1. anon lee SOLO filas status = 'published'.
--   2. insert/update/delete solo para un usuario de admin_users (is_admin()).
--   3. messages: anon inserta, nunca lee. Solo el admin lee.
--   4. storage: en la migracion siguiente.
--
-- Dos decisiones que evitan los fallos tipicos:
--
-- a) Politica de lectura del admin, separada de la publica. Las politicas
--    permissive se combinan con OR, asi que el admin ve TODO (incluidos los
--    borradores) sin que la politica publica deje de filtrar por status.
--    Sin esta politica, el panel /admin no veria los borradores que acaba de crear.
--
-- b) Nunca `for all`. Cada operacion lleva su politica, y update lleva `using`
--    (que filas puede tocar) y `with check` (como pueden quedar) por separado.

-- ------------------------------------------------- privilegios base (grants)
-- Defensa en profundidad: RLS decide QUE filas; los grants deciden que
-- operaciones puede intentar siquiera el rol. anon no tiene update ni delete
-- en ninguna tabla, aunque alguna politica se escribiera mal.

revoke all on all tables in schema public from anon, authenticated;

grant select on
  public.areas, public.subareas, public.profile, public.projects,
  public.project_subareas, public.project_media, public.experiences,
  public.certifications, public.education, public.publications, public.contacts
to anon, authenticated;

grant insert on public.messages to anon, authenticated;

-- El admin es un usuario `authenticated`; is_admin() lo distingue en cada politica.
grant select, insert, update, delete on
  public.admin_users, public.areas, public.subareas, public.profile,
  public.projects, public.project_subareas, public.project_media,
  public.experiences, public.certifications, public.education,
  public.publications, public.contacts, public.messages
to authenticated;

-- ------------------------------------------------------------- admin_users

alter table public.admin_users enable row level security;

-- Cada usuario ve su propia fila; el admin ve todas. is_admin() es security
-- definer, asi que su lectura interna de admin_users no reentra en esta politica.
create policy admin_users_select_propio on public.admin_users
  for select to authenticated
  using ((select auth.uid()) = user_id or public.is_admin());

create policy admin_users_insert_admin on public.admin_users
  for insert to authenticated
  with check (public.is_admin());

create policy admin_users_update_admin on public.admin_users
  for update to authenticated
  using (public.is_admin())
  with check (public.is_admin());

create policy admin_users_delete_admin on public.admin_users
  for delete to authenticated
  using (public.is_admin());

-- ------------------------------------------------------- taxonomia publica
-- areas y subareas no tienen `status` en el contrato: son el esqueleto de las
-- rutas y deben existir aunque no haya proyectos. Lectura abierta, escritura admin.

alter table public.areas enable row level security;
alter table public.subareas enable row level security;

create policy areas_select_publico on public.areas
  for select to anon, authenticated using (true);
create policy areas_insert_admin on public.areas
  for insert to authenticated with check (public.is_admin());
create policy areas_update_admin on public.areas
  for update to authenticated using (public.is_admin()) with check (public.is_admin());
create policy areas_delete_admin on public.areas
  for delete to authenticated using (public.is_admin());

create policy subareas_select_publico on public.subareas
  for select to anon, authenticated using (true);
create policy subareas_insert_admin on public.subareas
  for insert to authenticated with check (public.is_admin());
create policy subareas_update_admin on public.subareas
  for update to authenticated using (public.is_admin()) with check (public.is_admin());
create policy subareas_delete_admin on public.subareas
  for delete to authenticated using (public.is_admin());

-- ------------------------------------------ tablas de contenido con `status`
-- Mismas cinco politicas para las siete tablas. Se generan en bucle a proposito:
-- el fallo clasico es que una tabla se quede sin la politica de lectura del admin
-- y sus borradores desaparezcan del panel.

do $$
declare
  t text;
begin
  foreach t in array array[
    'profile', 'projects', 'experiences', 'certifications',
    'education', 'publications', 'contacts'
  ] loop
    execute format('alter table public.%I enable row level security', t);

    -- Regla 1: lectura publica limitada a lo publicado.
    execute format($f$
      create policy %I on public.%I
        for select to anon, authenticated
        using (status = 'published')
    $f$, t || '_select_publico', t);

    -- El admin ve tambien los borradores (permissive => OR con la anterior).
    execute format($f$
      create policy %I on public.%I
        for select to authenticated
        using (public.is_admin())
    $f$, t || '_select_admin', t);

    -- Regla 2: escritura solo del propietario.
    execute format($f$
      create policy %I on public.%I
        for insert to authenticated
        with check (public.is_admin())
    $f$, t || '_insert_admin', t);

    execute format($f$
      create policy %I on public.%I
        for update to authenticated
        using (public.is_admin())
        with check (public.is_admin())
    $f$, t || '_update_admin', t);

    execute format($f$
      create policy %I on public.%I
        for delete to authenticated
        using (public.is_admin())
    $f$, t || '_delete_admin', t);
  end loop;
end;
$$;

-- ------------------------------------ tablas hijas de projects (sin `status`)
-- Su visibilidad la hereda del proyecto padre. Sin este `exists`, anon podria
-- enumerar los medios y la taxonomia de un proyecto en borrador.

alter table public.project_subareas enable row level security;
alter table public.project_media enable row level security;

create policy project_subareas_select_publico on public.project_subareas
  for select to anon, authenticated
  using (exists (
    select 1 from public.projects p
    where p.id = project_id and p.status = 'published'
  ));

create policy project_subareas_select_admin on public.project_subareas
  for select to authenticated using (public.is_admin());

create policy project_subareas_insert_admin on public.project_subareas
  for insert to authenticated with check (public.is_admin());

create policy project_subareas_update_admin on public.project_subareas
  for update to authenticated using (public.is_admin()) with check (public.is_admin());

create policy project_subareas_delete_admin on public.project_subareas
  for delete to authenticated using (public.is_admin());

create policy project_media_select_publico on public.project_media
  for select to anon, authenticated
  using (exists (
    select 1 from public.projects p
    where p.id = project_id and p.status = 'published'
  ));

create policy project_media_select_admin on public.project_media
  for select to authenticated using (public.is_admin());

create policy project_media_insert_admin on public.project_media
  for insert to authenticated with check (public.is_admin());

create policy project_media_update_admin on public.project_media
  for update to authenticated using (public.is_admin()) with check (public.is_admin());

create policy project_media_delete_admin on public.project_media
  for delete to authenticated using (public.is_admin());

-- ---------------------------------------------------------------- messages
-- Regla 3. Deliberadamente NO hay politica de select para anon: sin politica,
-- RLS deniega. Ademas anon no tiene ni el privilegio select sobre la tabla.

alter table public.messages enable row level security;

-- El formulario de contacto no puede marcar su propio mensaje como leido.
create policy messages_insert_publico on public.messages
  for insert to anon, authenticated
  with check (read = false);

create policy messages_select_admin on public.messages
  for select to authenticated using (public.is_admin());

create policy messages_update_admin on public.messages
  for update to authenticated using (public.is_admin()) with check (public.is_admin());

create policy messages_delete_admin on public.messages
  for delete to authenticated using (public.is_admin());

-- --------------------------------------------------------------- red de seguridad
-- Falla la migracion si alguna tabla de `public` se queda sin RLS o sin politicas.
-- "Una tabla sin politica es una tabla abierta" — que no dependa de la revision humana.

do $$
declare
  sin_rls text;
  sin_politica text;
begin
  select string_agg(c.relname, ', ' order by c.relname) into sin_rls
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity;

  if sin_rls is not null then
    raise exception 'Tablas sin RLS activada: %', sin_rls;
  end if;

  select string_agg(c.relname, ', ' order by c.relname) into sin_politica
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r'
    and not exists (select 1 from pg_policy p where p.polrelid = c.oid);

  if sin_politica is not null then
    raise exception 'Tablas con RLS y sin ninguna politica: %', sin_politica;
  end if;
end;
$$;
