'use client';

import { useEffect, useRef } from 'react';

import { Button } from './ui';

/**
 * Confirmación de borrado. Enseña *qué* se borra, no un "¿estás seguro?" genérico:
 * si el aviso no dice el nombre, no es una confirmación, es un trámite.
 */
export default function ConfirmDialog({
  title,
  what,
  detail,
  busy,
  onCancel,
  onConfirm,
}: {
  title: string;
  what: string;
  detail?: string;
  busy?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-body"
        className="w-full max-w-md border border-content/30 bg-surface p-4"
      >
        <h2 id="confirm-title" className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted">
          {title}
        </h2>
        <p id="confirm-body" className="mt-3 text-[14px] text-content">
          Se va a borrar <strong className="font-semibold">{what}</strong>. La operación no se
          puede deshacer.
        </p>
        {detail && <p className="mt-2 text-[13px] text-muted">{detail}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <Button ref={cancelRef} onClick={onCancel} disabled={busy} type="button">
            Cancelar
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={busy} type="button">
            {busy ? 'Borrando…' : 'Borrar'}
          </Button>
        </div>
      </div>
    </div>
  );
}
