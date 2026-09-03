import Link from 'next/link';
import { notFound } from 'next/navigation';

import DataTable from '@/components/admin/DataTable';
import { Notice, Panel } from '@/components/admin/ui';
import { attempt } from '@/lib/admin/api';
import { listRows } from '@/lib/admin/data';
import { RESOURCES, isResourceKey } from '@/lib/admin/resources';

export const dynamic = 'force-dynamic';

export default async function ResourceListPage({
  params,
}: {
  params: Promise<{ resource: string }>;
}) {
  const { resource } = await params;
  if (!isResourceKey(resource)) notFound();
  const def = RESOURCES[resource];

  const result = await attempt(() => listRows(resource));

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="font-mono text-[12px] uppercase tracking-[0.18em] text-muted">
          {def.label}
        </h1>
        {def.canCreate && (
          <Link
            href={`/admin/${resource}/new`}
            className="bg-surface-inverted px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.1em] text-on-inverted hover:opacity-90"
          >
            {def.newLabel}
          </Link>
        )}
      </div>

      {def.note && <Notice tone="info">{def.note}</Notice>}

      {!result.ok ? (
        <Notice tone="error">No se pudo cargar el listado: {result.message}</Notice>
      ) : (
        <Panel>
          <DataTable resource={resource} rows={result.data} />
        </Panel>
      )}
    </div>
  );
}
