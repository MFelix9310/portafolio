-- Indices.
--
-- Los `unique` de slug y legacy_id ya crean su indice; no se repiten aqui.
-- El patron de consulta real del sitio es siempre el mismo:
--   where status = 'published' order by display_order
-- de ahi los indices compuestos parciales.

-- projects
create index projects_status_orden_idx
  on public.projects (display_order, created_at desc)
  where status = 'published';
create index projects_status_idx on public.projects (status);

-- project_subareas: la pk (project_id, subarea_id) cubre las busquedas por
-- proyecto; falta el sentido inverso, que es el de las rutas /data, /developer...
create index project_subareas_subarea_id_idx on public.project_subareas (subarea_id);

-- project_media
create index project_media_project_id_orden_idx
  on public.project_media (project_id, display_order);
create index project_media_kind_idx on public.project_media (project_id, kind);

-- experiences
create index experiences_status_orden_idx
  on public.experiences (display_order, start_date desc)
  where status = 'published';
create index experiences_status_idx on public.experiences (status);

-- certifications
create index certifications_status_orden_idx
  on public.certifications (display_order, issued_on desc)
  where status = 'published';
create index certifications_status_idx on public.certifications (status);

-- education
create index education_status_orden_idx
  on public.education (display_order, graduation_year desc)
  where status = 'published';
create index education_status_idx on public.education (status);

-- publications
create index publications_status_orden_idx
  on public.publications (display_order, published_on desc)
  where status = 'published';
create index publications_status_idx on public.publications (status);

-- contacts
create index contacts_status_orden_idx
  on public.contacts (display_order)
  where status = 'published';
create index contacts_status_idx on public.contacts (status);

-- profile
create index profile_status_idx on public.profile (status);

-- messages: la bandeja del admin se lee por no leidos y por fecha.
create index messages_created_at_idx on public.messages (created_at desc);
create index messages_no_leidos_idx on public.messages (created_at desc) where not read;
