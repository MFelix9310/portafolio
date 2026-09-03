'use client';

import type { UploadTicket } from './types';

/**
 * Sube el binario directamente a Storage con la URL firmada que emitió el backend.
 *
 * El fichero no pasa por FastAPI —sería tonto—, pero el permiso lo concede él y el
 * registro en `project_media` se crea después con un caso de uso. Se usa XHR y no
 * `fetch` por una razón concreta: `fetch` no informa del progreso de subida, y la
 * especificación pide barra real, no un spinner indefinido.
 */
export function uploadToStorage(
  file: File,
  ticket: UploadTicket,
  onProgress: (percent: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open('PUT', ticket.upload_url, true);
    request.setRequestHeader('content-type', file.type || 'application/octet-stream');
    if (ticket.token) request.setRequestHeader('authorization', `Bearer ${ticket.token}`);
    request.setRequestHeader('x-upsert', 'true');

    request.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
    });
    request.addEventListener('load', () => {
      if (request.status >= 200 && request.status < 300) {
        onProgress(100);
        resolve();
        return;
      }
      reject(new Error(`Storage respondió ${request.status}: ${request.responseText.slice(0, 200)}`));
    });
    request.addEventListener('error', () => reject(new Error('la subida falló en la red')));
    request.addEventListener('abort', () => reject(new Error('subida cancelada')));
    request.send(file);
  });
}

/** El adaptador local de desarrollo firma una URL que no existe; se dice, no se finge. */
export function isDevUploadTicket(ticket: UploadTicket): boolean {
  return ticket.upload_url.includes('/dev-upload/');
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} kB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
