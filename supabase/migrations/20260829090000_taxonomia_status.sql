-- `status` en areas y subareas.
--
-- El contrato original no se lo daba, asi que su select publica era `using (true)`:
-- retirar un chip de area o subarea del panel obligaba a BORRAR la fila, y con ella
-- se perdian los vinculos de project_subareas. Con `status` se puede despublicar y
-- recuperar despues sin tocar los datos.
--
-- Por defecto 'published', no 'draft': las tres areas y sus diez subareas ya existen
-- y el sitio no puede nacer sin navegacion. El `default` tambien rellena las filas
-- que la semilla fija creo en 20260828120200_taxonomia.sql.

alter table public.areas
  add column if not exists status text not null default 'published'
    check (status in ('draft', 'published'));

alter table public.subareas
  add column if not exists status text not null default 'published'
    check (status in ('draft', 'published'));

create index if not exists areas_status_idx on public.areas (status);
create index if not exists subareas_status_idx on public.subareas (status);

-- ------------------------------------------------------- select publica: por status
-- Sustituye el `using (true)` de 20260828120600_rls.sql.

drop policy if exists areas_select_publico on public.areas;
create policy areas_select_publico on public.areas
  for select to anon, authenticated
  using (status = 'published');

-- Una subarea de un area despublicada no debe verse: dejaria un chip huerfano
-- apuntando a una seccion que ya no existe. Mismo patron que project_media
-- respecto a su proyecto padre.
drop policy if exists subareas_select_publico on public.subareas;
create policy subareas_select_publico on public.subareas
  for select to anon, authenticated
  using (
    status = 'published'
    and exists (
      select 1 from public.areas a
      where a.id = area_id and a.status = 'published'
    )
  );

-- --------------------------------------------------- select del admin: ve todo
-- Estas politicas NO existian: con `using (true)` el admin ya lo veia todo. Al
-- filtrar ahora por status hay que anadirlas, o el panel dejaria de ver las
-- areas y subareas que acaba de despublicar y no podria volver a publicarlas.

drop policy if exists areas_select_admin on public.areas;
create policy areas_select_admin on public.areas
  for select to authenticated
  using (public.is_admin());

drop policy if exists subareas_select_admin on public.subareas;
create policy subareas_select_admin on public.subareas
  for select to authenticated
  using (public.is_admin());
