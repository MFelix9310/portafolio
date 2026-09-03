-- Regla 4 del contrato: bucket `media` publico en lectura, escritura y borrado
-- solo para el admin autenticado.

insert into storage.buckets (id, name, public, file_size_limit)
values ('media', 'media', true, 52428800)  -- 50 MiB, igual que config.toml
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit;

-- storage.objects ya tiene RLS activada por Supabase. Aqui solo se anaden las
-- politicas del bucket `media`; no se tocan las de otros buckets.
--
-- El bucket es `public = true`, asi que la descarga por URL publica no pasa por
-- esta politica. La politica de select hace falta igualmente para poder LISTAR
-- el contenido del bucket (la API de list si aplica RLS).

drop policy if exists media_select_publico on storage.objects;
create policy media_select_publico on storage.objects
  for select to anon, authenticated
  using (bucket_id = 'media');

drop policy if exists media_insert_admin on storage.objects;
create policy media_insert_admin on storage.objects
  for insert to authenticated
  with check (bucket_id = 'media' and public.is_admin());

-- `using` limita que objetos puede mover o renombrar; `with check` impide que el
-- resultado acabe fuera del bucket `media`.
drop policy if exists media_update_admin on storage.objects;
create policy media_update_admin on storage.objects
  for update to authenticated
  using (bucket_id = 'media' and public.is_admin())
  with check (bucket_id = 'media' and public.is_admin());

drop policy if exists media_delete_admin on storage.objects;
create policy media_delete_admin on storage.objects
  for delete to authenticated
  using (bucket_id = 'media' and public.is_admin());
