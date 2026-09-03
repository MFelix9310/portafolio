'use client';

import { useState, useTransition } from 'react';

import { revalidateAction } from '@/lib/admin/actions';
import { Button } from './ui';

/**
 * Revalidación manual del sitio público. Se dispara sola al publicar; este botón
 * existe para cuando algo se ha quedado atrás y hay que forzarla sin volver a
 * guardar nada.
 */
export default function RevalidateButton() {
  const [message, setMessage] = useState('');
  const [pending, startTransition] = useTransition();

  return (
    <span className="flex items-center gap-2">
      <Button
        type="button"
        disabled={pending}
        onClick={() =>
          startTransition(async () => {
            const result = await revalidateAction();
            setMessage(result.message ?? (result.ok ? 'Hecho.' : 'Falló.'));
          })
        }
      >
        {pending ? 'Revalidando…' : 'Revalidar sitio'}
      </Button>
      <span aria-live="polite" className="text-[12px] text-muted">
        {message}
      </span>
    </span>
  );
}
