'use client';

import { useState } from 'react';

import FileUploader, { type UploadAccept } from './FileUploader';
import { Button } from './ui';

/**
 * Ruta de Storage. Se guarda verbatim, con el prefijo del bucket (addendum A4):
 * `media/projects/...`. El campo es editable a mano porque el contenido heredado
 * ya tiene rutas válidas que no hace falta volver a subir.
 */
export default function PathInput({
  id,
  value,
  accept,
  onChange,
  describedBy,
}: {
  id: string;
  value: string;
  accept?: UploadAccept;
  onChange: (next: string) => void;
  describedBy?: string;
}) {
  const [uploading, setUploading] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          id={id}
          type="text"
          value={value}
          aria-describedby={describedBy}
          placeholder="media/projects/…"
          onChange={(event) => onChange(event.target.value)}
          className="w-full border border-content/25 bg-surface px-2 py-1.5 font-mono text-[12px] text-content placeholder:text-faint"
        />
        <Button type="button" onClick={() => setUploading((open) => !open)} aria-expanded={uploading}>
          {uploading ? 'Cerrar' : 'Subir'}
        </Button>
      </div>
      {uploading && (
        <FileUploader
          accept={accept}
          label="Subir y usar"
          onUploaded={({ ticket }) => {
            onChange(ticket.storage_path);
            setUploading(false);
          }}
        />
      )}
    </div>
  );
}
