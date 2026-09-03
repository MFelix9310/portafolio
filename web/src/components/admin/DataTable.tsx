'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, useTransition } from 'react';

import { deleteResourceAction, reorderAction, setStatusAction } from '@/lib/admin/actions';
import { RESOURCES, type ResourceKey } from '@/lib/admin/resources';
import type { AdminRow, Status } from '@/lib/admin/types';
import Cell from './TableCell';
import ConfirmDialog from './ConfirmDialog';
import { Button, EmptyState, StatusBadge } from './ui';

export default function DataTable({
  resource,
  rows: initialRows,
}: {
  resource: ResourceKey;
  rows: AdminRow[];
}) {
  const def = RESOURCES[resource];
  const router = useRouter();
  const [rows, setRows] = useState(initialRows);
  const [target, setTarget] = useState<AdminRow | null>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [pending, startTransition] = useTransition();

  const announce = (message: string) => setFeedback(message);

  function move(index: number, delta: number) {
    const next = [...rows];
    const swap = index + delta;
    const a = next[index];
    const b = next[swap];
    if (!a || !b) return;
    next[index] = b;
    next[swap] = a;
    setRows(next);
    const ids = next.map((row) => row.id).filter((id): id is string => Boolean(id));
    startTransition(async () => {
      const result = await reorderAction(resource, ids);
      announce(result.ok ? 'Orden guardado.' : `No se pudo reordenar: ${result.message}`);
      if (!result.ok) setRows(initialRows);
      else router.refresh();
    });
  }

  function toggleStatus(row: AdminRow) {
    if (!row.id) return;
    const next: Status = row.status === 'published' ? 'draft' : 'published';
    setRows((current) => current.map((r) => (r.id === row.id ? { ...r, status: next } : r)));
    startTransition(async () => {
      const result = await setStatusAction(resource, row.id as string, next);
      announce(
        result.ok
          ? `${def.singular} ${next === 'published' ? 'publicado' : 'pasado a borrador'}.`
          : `No se pudo cambiar el estado: ${result.message}`,
      );
      if (!result.ok) setRows(initialRows);
      else router.refresh();
    });
  }

  function confirmDelete() {
    const row = target;
    if (!row?.id) return;
    startTransition(async () => {
      const result = await deleteResourceAction(resource, row.id as string);
      if (result.ok) {
        setRows((current) => current.filter((r) => r.id !== row.id));
        announce('Borrado.');
        setTarget(null);
        router.refresh();
      } else {
        announce(`No se pudo borrar: ${result.message}`);
        setTarget(null);
      }
    });
  }

  if (rows.length === 0) {
    return <EmptyState>Todavía no hay {def.label.toLowerCase()}.</EmptyState>;
  }

  return (
    <>
      <p aria-live="polite" className="sr-only">
        {feedback}
      </p>
      {feedback && (
        <p className="border-b border-content/15 px-3 py-1.5 text-[12px] text-muted">{feedback}</p>
      )}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-[13px]">
          <caption className="sr-only">{def.label}</caption>
          <thead>
            <tr className="border-b border-content/25 text-left">
              {def.canReorder && <th scope="col" className="w-16 px-2 py-1.5 sr-only">Orden</th>}
              {def.columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={`px-2 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-muted ${column.width ?? ''}`}
                >
                  {column.label}
                </th>
              ))}
              <th scope="col" className="w-40 px-2 py-1.5 text-right font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={row.id ?? index} className="border-b border-content/10 hover:bg-surface-sunken">
                {def.canReorder && (
                  <td className="px-1 py-1 align-top">
                    <div className="flex gap-0.5">
                      <Button
                        variant="quiet"
                        type="button"
                        className="px-1 py-0.5"
                        disabled={index === 0 || pending}
                        onClick={() => move(index, -1)}
                        aria-label={`Subir ${def.titleOf(row)}`}
                      >
                        ↑
                      </Button>
                      <Button
                        variant="quiet"
                        type="button"
                        className="px-1 py-0.5"
                        disabled={index === rows.length - 1 || pending}
                        onClick={() => move(index, 1)}
                        aria-label={`Bajar ${def.titleOf(row)}`}
                      >
                        ↓
                      </Button>
                    </div>
                  </td>
                )}
                {def.columns.map((column) => (
                  <td key={column.key} className="px-2 py-1.5 align-top">
                    {column.kind === 'status' ? (
                      <StatusBadge status={String(row[column.key] ?? 'draft')} />
                    ) : (
                      <Cell kind={column.kind} value={row[column.key]} />
                    )}
                  </td>
                ))}
                <td className="px-2 py-1.5 text-right align-top">
                  <div className="flex justify-end gap-1">
                    {row.id && (
                      <Link
                        href={`/admin/${resource}/${row.id}`}
                        className="border border-content/25 px-2 py-1 font-mono text-[10px] uppercase tracking-[0.1em] text-content hover:bg-surface-sunken"
                      >
                        Editar
                      </Link>
                    )}
                    {def.hasStatus && row.id && (
                      <Button
                        type="button"
                        variant="quiet"
                        disabled={pending}
                        onClick={() => toggleStatus(row)}
                      >
                        {row.status === 'published' ? 'Despublicar' : 'Publicar'}
                      </Button>
                    )}
                    {def.canDelete && row.id && (
                      <Button
                        type="button"
                        variant="quiet"
                        disabled={pending}
                        onClick={() => setTarget(row)}
                        aria-label={`Borrar ${def.titleOf(row)}`}
                      >
                        Borrar
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {target && (
        <ConfirmDialog
          title={`Borrar ${def.singular}`}
          what={def.titleOf(target)}
          detail={
            resource === 'projects'
              ? 'También desaparecen sus etiquetas de área y su media asociada.'
              : undefined
          }
          busy={pending}
          onCancel={() => setTarget(null)}
          onConfirm={confirmDelete}
        />
      )}
    </>
  );
}
