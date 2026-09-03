'use client';

import { useRef, useState } from 'react';

import { createUploadUrlAction } from '@/lib/admin/actions';
import { VIDEO_WARN_BYTES } from '@/lib/admin/config';
import type { UploadTicket } from '@/lib/admin/types';
import { formatBytes, isDevUploadTicket, uploadToStorage } from '@/lib/admin/upload';
import { Button, Notice } from './ui';

const ACCEPT = {
  image: 'image/*',
  video: 'video/*',
  document: '.pdf,.csv,.xlsx,.docx,application/pdf',
  any: undefined,
} as const;

export type UploadAccept = keyof typeof ACCEPT;

export interface UploadResult {
  ticket: UploadTicket;
  file: File;
}

/**
 * Selección de fichero, URL firmada, subida con progreso real.
 *
 * El aviso de vídeo pesado informa, no bloquea: la especificación es explícita en
 * que Félix debe poder subirlo igualmente si sabe lo que hace.
 */
export default function FileUploader({
  accept = 'any',
  label = 'Subir fichero',
  onUploaded,
}: {
  accept?: UploadAccept;
  label?: string;
  onUploaded: (result: UploadResult) => void | Promise<void>;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [percent, setPercent] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [devNote, setDevNote] = useState('');

  const heavyVideo =
    file !== null && file.type.startsWith('video/') && file.size > VIDEO_WARN_BYTES;

  async function start() {
    if (!file) return;
    setError('');
    setDevNote('');
    setPercent(0);

    const ticketResult = await createUploadUrlAction(
      file.name,
      file.type || 'application/octet-stream',
    );
    if (!ticketResult.ok || !ticketResult.data) {
      setPercent(null);
      setError(ticketResult.message ?? 'No se pudo firmar la subida.');
      return;
    }
    const ticket = ticketResult.data;

    try {
      await uploadToStorage(file, ticket, setPercent);
    } catch (cause) {
      if (isDevUploadTicket(ticket)) {
        // El adaptador local no tiene endpoint de subida. Se registra la ruta igual
        // para poder ejercitar el panel, y se dice claramente que el binario no viajó.
        setDevNote('Modo desarrollo: no hay Storage real, sólo se registra la ruta.');
        setPercent(100);
      } else {
        setPercent(null);
        setError((cause as Error).message);
        return;
      }
    }

    await onUploaded({ ticket, file });
    setFile(null);
    setPercent(null);
    if (inputRef.current) inputRef.current.value = '';
  }

  const busy = percent !== null;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT[accept]}
          aria-label={label}
          disabled={busy}
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setError('');
            setDevNote('');
          }}
          className="max-w-full text-[12px] text-muted file:mr-2 file:border file:border-content/25 file:bg-surface file:px-2 file:py-1 file:font-mono file:text-[10px] file:uppercase file:tracking-[0.1em] file:text-content"
        />
        <Button type="button" variant="primary" disabled={!file || busy} onClick={start}>
          {busy ? 'Subiendo…' : label}
        </Button>
      </div>

      {file && (
        <p className="font-mono text-[11px] text-muted">
          {file.name} · {formatBytes(file.size)}
        </p>
      )}

      {heavyVideo && (
        <Notice tone="info">
          Vídeo de {formatBytes(file.size)}: por encima de 15 MB conviene pasarlo antes por{' '}
          <code className="font-mono">tools/media</code> (genera 720p y 1080p y un póster
          WebP). Supabase Storage no transcodifica. Puedes subirlo igualmente.
        </Notice>
      )}

      {busy && (
        <div>
          <div
            role="progressbar"
            aria-valuenow={percent ?? 0}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Progreso de la subida"
            className="h-1.5 w-full border border-content/25 bg-surface-sunken"
          >
            <div className="h-full bg-structure transition-[width]" style={{ width: `${percent}%` }} />
          </div>
          <p className="mt-1 font-mono text-[11px] tabular-nums text-muted">{percent}%</p>
        </div>
      )}

      {devNote && <Notice tone="info">{devNote}</Notice>}
      {error && <Notice tone="error">{error}</Notice>}
    </div>
  );
}
