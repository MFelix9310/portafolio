'use client';

import { useRouter } from 'next/navigation';
import { useState, useTransition } from 'react';

import { deleteMediaAction, reorderMediaAction, saveMediaAction } from '@/lib/admin/actions';
import type { AdminMedia } from '@/lib/admin/types';
import ConfirmDialog from './ConfirmDialog';
import FileUploader from './FileUploader';
import { Button, EmptyState, Notice, Panel } from './ui';

function kindOf(file: File): 'image' | 'video' | 'document' {
  if (file.type.startsWith('image/')) return 'image';
  if (file.type.startsWith('video/')) return 'video';
  return 'document';
}

/**
 * Media de un proyecto. El binario va del navegador a Storage con la URL firmada,
 * pero la fila de `project_media` la crea `POST /admin/media`, que ejecuta un caso
 * de uso: el panel no escribe en Postgres por su cuenta.
 */
export default function MediaPanel({
  projectId,
  media: initial,
}: {
  projectId: string;
  media: AdminMedia[];
}) {
  const router = useRouter();
  const [media, setMedia] = useState(initial);
  const [target, setTarget] = useState<AdminMedia | null>(null);
  const [error, setError] = useState('');
  const [pending, startTransition] = useTransition();

  async function register(storagePath: string, kind: 'image' | 'video' | 'document') {
    const result = await saveMediaAction({
      project_id: projectId,
      kind,
      storage_path: storagePath,
      display_order: media.length,
    });
    if (!result.ok || !result.data) {
      setError(result.message ?? 'No se pudo registrar el fichero.');
      return;
    }
    setError('');
    setMedia((current) => [...current, result.data as AdminMedia]);
    router.refresh();
  }

  function move(index: number, delta: number) {
    const next = [...media];
    const a = next[index];
    const b = next[index + delta];
    if (!a || !b) return;
    next[index] = b;
    next[index + delta] = a;
    setMedia(next);
    const ids = next.map((item) => item.id).filter((id): id is string => Boolean(id));
    startTransition(async () => {
      const result = await reorderMediaAction(ids);
      if (!result.ok) {
        setError(result.message ?? 'No se pudo reordenar.');
        setMedia(initial);
      } else router.refresh();
    });
  }

  function remove() {
    const item = target;
    if (!item?.id) return;
    startTransition(async () => {
      const result = await deleteMediaAction(item.id as string);
      if (result.ok) {
        setMedia((current) => current.filter((entry) => entry.id !== item.id));
        router.refresh();
      } else setError(result.message ?? 'No se pudo borrar.');
      setTarget(null);
    });
  }

  return (
    <Panel title={`Media · ${media.length}`}>
      <div className="border-b border-content/15 p-3">
        <FileUploader
          label="Subir a este proyecto"
          onUploaded={({ ticket, file }) => register(ticket.storage_path, kindOf(file))}
        />
        {error && (
          <div className="mt-2">
            <Notice tone="error">{error}</Notice>
          </div>
        )}
      </div>

      {media.length === 0 ? (
        <EmptyState>Este proyecto no tiene media.</EmptyState>
      ) : (
        <ul>
          {media.map((item, index) => (
            <li
              key={item.id ?? item.storage_path}
              className="flex items-center gap-3 border-b border-content/10 px-3 py-2"
            >
              {item.kind === 'image' && item.storage_url ? (
                // `<img>` crudo a propósito (D8): miniatura de 40×56 con tamaño
                // fijo —ni CLS ni bytes que ganar— y la URL viene tal cual de la
                // fila. Si apuntara a un host fuera de `remotePatterns`,
                // `next/image` daría un 400 y Félix vería rota la imagen que
                // acaba de subir. Un `<img>` degrada; el optimizador falla.
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={item.storage_url}
                  alt=""
                  className="h-10 w-14 border border-content/15 object-cover"
                />
              ) : (
                <span className="flex h-10 w-14 items-center justify-center border border-content/15 font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                  {item.kind}
                </span>
              )}
              <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-muted">
                {item.storage_path}
              </span>
              <div className="flex gap-1">
                <Button
                  type="button"
                  variant="quiet"
                  className="px-1 py-0.5"
                  disabled={index === 0 || pending}
                  onClick={() => move(index, -1)}
                  aria-label={`Subir ${item.storage_path}`}
                >
                  ↑
                </Button>
                <Button
                  type="button"
                  variant="quiet"
                  className="px-1 py-0.5"
                  disabled={index === media.length - 1 || pending}
                  onClick={() => move(index, 1)}
                  aria-label={`Bajar ${item.storage_path}`}
                >
                  ↓
                </Button>
                <Button
                  type="button"
                  variant="quiet"
                  disabled={pending}
                  onClick={() => setTarget(item)}
                  aria-label={`Borrar ${item.storage_path}`}
                >
                  Borrar
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {target && (
        <ConfirmDialog
          title="Borrar media"
          what={target.storage_path}
          detail="Se elimina el registro del proyecto. El fichero permanece en Storage."
          busy={pending}
          onCancel={() => setTarget(null)}
          onConfirm={remove}
        />
      )}
    </Panel>
  );
}
