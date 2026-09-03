import { EmptyState, Notice, Panel } from '@/components/admin/ui';
import { adminApi, attempt } from '@/lib/admin/api';
import type { AdminMessage } from '@/lib/admin/types';

export const dynamic = 'force-dynamic';

/** Solo lectura: los mensajes del formulario de contacto no se editan ni se borran. */
export default async function MessagesPage() {
  const result = await attempt(() => adminApi.get<AdminMessage[]>('/admin/messages'));

  return (
    <div className="space-y-3">
      <h1 className="font-mono text-[12px] uppercase tracking-[0.18em] text-muted">Mensajes</h1>
      {!result.ok ? (
        <Notice tone="error">No se pudieron cargar: {result.message}</Notice>
      ) : (
        <Panel>
          {result.data.length === 0 ? (
            <EmptyState>Todavía no hay mensajes.</EmptyState>
          ) : (
            <ul>
              {result.data.map((message, index) => (
                <li key={message.id ?? index} className="border-b border-content/10 px-3 py-2">
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="text-[14px] font-semibold">{message.name}</span>
                    <a
                      href={`mailto:${message.email}`}
                      className="font-mono text-[11px] text-structure hover:underline"
                    >
                      {message.email}
                    </a>
                    <time
                      dateTime={message.created_at}
                      className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint"
                    >
                      {message.created_at.slice(0, 16).replace('T', ' ')}
                    </time>
                    {!message.read && (
                      <span className="border border-accent-text/50 px-1 font-mono text-[9px] uppercase tracking-[0.12em] text-accent-text">
                        Sin leer
                      </span>
                    )}
                  </div>
                  {message.subject && (
                    <p className="mt-1 text-[13px] font-medium">{message.subject}</p>
                  )}
                  <p className="mt-1 whitespace-pre-wrap text-[13px] text-muted">{message.body}</p>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      )}
    </div>
  );
}
