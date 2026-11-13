-- Subarea de Civil BIM para los proyectos realizados: edificios con juego de
-- planos, que el sitio pinta en un apartado propio y no en la rejilla de
-- herramientas. Idempotente para poder repetirse.

insert into public.subareas (area_id, key, name, display_order)
select a.id, 'completed', '{"es": "Proyectos realizados", "en": "Completed projects"}'::jsonb, 0
from public.areas a
where a.key = 'civil-bim'
on conflict do nothing;
