'use client';

import { useEffect } from 'react';

const MESSAGE = 'Hay cambios sin guardar. ¿Salir y perderlos?';

/**
 * Aviso al salir con cambios sin guardar.
 *
 * `beforeunload` cubre recargar y cerrar la pestaña. La navegación interna del App
 * Router no emite eventos que se puedan cancelar, así que se intercepta el clic en
 * el enlace antes de que el router lo vea. No es elegante, pero perder un texto
 * largo escrito a mano es la forma más rápida de que un panel deje de usarse.
 */
export function useUnsavedChanges(dirty: boolean): void {
  useEffect(() => {
    if (!dirty) return;

    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };

    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey) return;
      const anchor = (event.target as HTMLElement | null)?.closest?.('a[href]');
      if (!(anchor instanceof HTMLAnchorElement)) return;
      if (anchor.target === '_blank' || anchor.hasAttribute('download')) return;
      const url = new URL(anchor.href, window.location.href);
      if (url.origin !== window.location.origin) return;
      if (url.pathname === window.location.pathname) return;
      if (!window.confirm(MESSAGE)) {
        event.preventDefault();
        event.stopPropagation();
      }
    };

    window.addEventListener('beforeunload', onBeforeUnload);
    document.addEventListener('click', onClick, true);
    return () => {
      window.removeEventListener('beforeunload', onBeforeUnload);
      document.removeEventListener('click', onClick, true);
    };
  }, [dirty]);
}
