import Link from 'next/link';

import { Notice } from '@/components/admin/ui';
import { adminApi, attempt } from '@/lib/admin/api';
import { listRows } from '@/lib/admin/data';
import { RESOURCE_KEYS, RESOURCES } from '@/lib/admin/resources';
import type { AdminMessage } from '@/lib/admin/types';

export const dynamic = 'force-dynamic';

interface Tally {
  key: string;
  label: string;
  total: number | null;
  drafts: number;
  error?: string;
}

export default async function DashboardPage() {
  const tallies: Tally[] = await Promise.all(
    RESOURCE_KEYS.map(async (key) => {
      const result = await attempt(() => listRows(key));
      if (!result.ok) {
        return { key, label: RESOURCES[key].label, total: null, drafts: 0, error: result.message };
      }
      return {
        key,
        label: RESOURCES[key].label,
        total: result.data.length,
        drafts: result.data.filter((row) => row.status === 'draft').length,
      };
    }),
  );

  const messages = await attempt(() => adminApi.get<AdminMessage[]>('/admin/messages'));
  const unread = messages.ok ? messages.data.filter((item) => !item.read).length : 0;
  const broken = tallies.find((item) => item.error);

  return (
    <div className="space-y-4">
      <h1 className="font-mono text-[12px] uppercase tracking-[0.18em] text-muted">Resumen</h1>

      {broken && (
        <Notice tone="error">
          No se pudo leer <strong>{broken.label}</strong>: {broken.error}
        </Notice>
      )}

      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {tallies.map((item) => (
          <li key={item.key}>
            <Link
              href={`/admin/${item.key}`}
              className="block border border-content/15 px-3 py-3 hover:bg-surface-sunken"
            >
              <span className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
                {item.label}
              </span>
              <span className="mt-1 block font-display text-3xl tabular-nums">
                {item.total ?? '—'}
              </span>
              {item.drafts > 0 && (
                <span className="mt-1 block font-mono text-[10px] uppercase tracking-[0.1em] text-accent-text">
                  {item.drafts} en borrador
                </span>
              )}
            </Link>
          </li>
        ))}
        <li>
          <Link
            href="/admin/messages"
            className="block border border-content/15 px-3 py-3 hover:bg-surface-sunken"
          >
            <span className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
              Mensajes
            </span>
            <span className="mt-1 block font-display text-3xl tabular-nums">
              {messages.ok ? messages.data.length : '—'}
            </span>
            {unread > 0 && (
              <span className="mt-1 block font-mono text-[10px] uppercase tracking-[0.1em] text-accent-text">
                {unread} sin leer
              </span>
            )}
          </Link>
        </li>
      </ul>

      <Notice tone="info">
        Los borradores solo se ven aquí y en la vista previa. Al publicar se dispara la
        revalidación del sitio; si algo no aparece, usa «Revalidar sitio».
      </Notice>
    </div>
  );
}
