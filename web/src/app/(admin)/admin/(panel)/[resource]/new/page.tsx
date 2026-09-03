import Link from 'next/link';
import { notFound } from 'next/navigation';

import ResourceForm from '@/components/admin/ResourceForm';
import { Notice, Panel } from '@/components/admin/ui';
import { attempt } from '@/lib/admin/api';
import { subareaOptions } from '@/lib/admin/data';
import { RESOURCES, isResourceKey } from '@/lib/admin/resources';

export const dynamic = 'force-dynamic';

export default async function NewResourcePage({
  params,
}: {
  params: Promise<{ resource: string }>;
}) {
  const { resource } = await params;
  if (!isResourceKey(resource)) notFound();
  const def = RESOURCES[resource];
  // A10: las áreas no se crean. Si alguien llega por URL, se le dice por qué.
  if (!def.canCreate) notFound();

  const subareas = await attempt(() => subareaOptions());

  return (
    <div className="space-y-3">
      <nav className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
        <Link href={`/admin/${resource}`} className="hover:text-content">
          ← {def.label}
        </Link>
      </nav>
      <h1 className="font-mono text-[12px] uppercase tracking-[0.18em] text-muted">
        {def.newLabel}
      </h1>
      {!subareas.ok && <Notice tone="error">Subáreas no disponibles: {subareas.message}</Notice>}
      <Panel>
        <div className="p-3">
          <ResourceForm
            resource={resource}
            id={null}
            subareas={subareas.ok ? subareas.data : []}
          />
        </div>
      </Panel>
    </div>
  );
}
