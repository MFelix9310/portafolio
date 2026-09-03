import Link from 'next/link';
import { notFound } from 'next/navigation';

import MediaPanel from '@/components/admin/MediaPanel';
import ResourceForm from '@/components/admin/ResourceForm';
import { Notice, Panel, StatusBadge } from '@/components/admin/ui';
import { attempt } from '@/lib/admin/api';
import { findRow, subareaOptions } from '@/lib/admin/data';
import { RESOURCES, isResourceKey } from '@/lib/admin/resources';
import type { AdminMedia } from '@/lib/admin/types';

export const dynamic = 'force-dynamic';

/**
 * Enlace a la página pública de esta fila, **si existe**.
 *
 * Antes esto apuntaba a `?preview=1` prometiendo ver borradores. No lo hacía
 * nadie: ninguna ruta pública lee `searchParams`, así que en un borrador el
 * enlace llevaba a un 404 y en un publicado el parámetro se ignoraba. Un enlace
 * que lleva a una página que no existe es peor que no tener enlace, así que
 * ahora sólo se pinta cuando la página pública está realmente publicada.
 *
 * La vista previa de borradores necesita datos que hoy el backend no expone
 * (no hay `GET /admin/catalog` ni `include_drafts` en el `/catalog` público);
 * está anotado en `docs/04-panel-admin.md`.
 */
function publicHref(resource: string, row: Record<string, unknown>): string | null {
  const published = String(row.status ?? '') === 'published';
  if (resource === 'projects' && typeof row.slug === 'string' && published) {
    return `/proyectos/${row.slug}`;
  }
  // Las tres áreas son rutas fijas del sitio: siempre existen.
  if (resource === 'areas' && typeof row.key === 'string') return `/${row.key}`;
  return null;
}

export default async function EditResourcePage({
  params,
}: {
  params: Promise<{ resource: string; id: string }>;
}) {
  const { resource, id } = await params;
  if (!isResourceKey(resource)) notFound();
  const def = RESOURCES[resource];

  const [rowResult, subareas] = await Promise.all([
    attempt(() => findRow(resource, id)),
    attempt(() => subareaOptions()),
  ]);

  if (!rowResult.ok) {
    return <Notice tone="error">No se pudo cargar: {rowResult.message}</Notice>;
  }
  const row = rowResult.data;
  if (!row) notFound();

  const publicUrl = publicHref(resource, row);
  const media = (row.media as AdminMedia[] | undefined) ?? [];

  return (
    <div className="space-y-3">
      <nav className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
        <Link href={`/admin/${resource}`} className="hover:text-content">
          ← {def.label}
        </Link>
      </nav>

      <div className="flex flex-wrap items-center gap-3">
        <h1 className="font-mono text-[12px] uppercase tracking-[0.18em] text-muted">
          {def.titleOf(row)}
        </h1>
        {def.hasStatus && <StatusBadge status={String(row.status ?? 'draft')} />}
        {publicUrl && (
          <Link
            href={publicUrl}
            target="_blank"
            className="font-mono text-[10px] uppercase tracking-[0.12em] text-structure hover:underline"
          >
            Ver en el sitio ↗
          </Link>
        )}
      </div>

      {!subareas.ok && <Notice tone="error">Subáreas no disponibles: {subareas.message}</Notice>}

      <Panel>
        <div className="p-3">
          <ResourceForm
            resource={resource}
            id={id}
            row={row}
            subareas={subareas.ok ? subareas.data : []}
          />
        </div>
      </Panel>

      {resource === 'projects' && <MediaPanel projectId={id} media={media} />}
    </div>
  );
}
