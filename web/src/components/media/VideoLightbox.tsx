'use client';

import { useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';
import type { ProjectMedia } from '@/lib/api/types';

interface VideoLightboxProps {
  media: ProjectMedia;
  title: string;
  locale: Locale;
  onClose: () => void;
}

const FOCUSABLE = 'button, [href], video, [tabindex]:not([tabindex="-1"])';

/**
 * Reproductor a pantalla casi completa (92 vw, lo que pidió el dueño del sitio).
 * La rendition 720 se sirve en viewports pequeños y la 1080 a partir de 900 px:
 * el navegador elige el primer `<source>` cuyo `media` case.
 */
export function VideoLightbox({ media, title, locale, onClose }: VideoLightboxProps) {
  const c = copy(locale);
  const dialog = useRef<HTMLDivElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  const handleKey = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== 'Tab' || !dialog.current) return;

      // Foco atrapado: el tabulador no puede salir del diálogo mientras esté abierto.
      const items = Array.from(dialog.current.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) return;
      const first = items[0]!;
      const last = items[items.length - 1]!;
      const active = document.activeElement;

      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    },
    [onClose],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeButton.current?.focus();

    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [handleKey]);

  const hd = media.renditions?.['1080'];
  const sd = media.renditions?.['720'];
  const weight = ((hd ?? sd)?.bytes ?? 0) / 1024 / 1024;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/95 p-4 backdrop-blur-[2px]"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-label={`${c.chrome.video.dialog} — ${title}`}
        className="relative w-[92vw] max-w-[92vw]"
      >
        <div className="mb-2 flex items-end justify-between gap-4">
          <Annotation className="!text-paper/70">{title}</Annotation>
          <button
            ref={closeButton}
            type="button"
            onClick={onClose}
            className="relative border border-paper/40 px-3 py-1.5 font-mono text-note uppercase tracking-[0.14em] text-paper transition-colors duration-200 hover:bg-paper hover:text-ink"
          >
            {c.chrome.video.close} · esc
          </button>
        </div>

        <div className="relative bg-ink">
          <CornerTicks size={14} className="text-paper/60" />
          <video
            controls
            autoPlay
            playsInline
            preload="auto"
            poster={media.poster ?? undefined}
            className="block max-h-[82vh] w-full"
          >
            {hd ? <source media="(min-width: 900px)" src={hd.src} type="video/mp4" /> : null}
            {sd ? <source src={sd.src} type="video/mp4" /> : null}
            {hd || sd ? null : <source src={media.src} type="video/mp4" />}
            {c.chrome.video.unsupported}
          </video>
        </div>

        <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1">
          {media.durationSeconds ? (
            <Annotation className="!text-paper/60">
              {c.chrome.video.duration} {Math.round(media.durationSeconds)}s
            </Annotation>
          ) : null}
          {weight > 0 ? (
            <Annotation className="!text-paper/60">
              {c.chrome.video.size} {weight.toFixed(1)} MB
            </Annotation>
          ) : null}
        </div>
      </div>
    </div>,
    document.body,
  );
}

export default VideoLightbox;
