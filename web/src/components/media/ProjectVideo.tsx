'use client';

import Image from 'next/image';
import { useRef, useState } from 'react';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import VideoLightbox from './VideoLightbox';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';
import type { ProjectMedia } from '@/lib/api/types';

interface ProjectVideoProps {
  media: ProjectMedia;
  title: string;
  locale: Locale;
  className?: string;
}

/**
 * En la tarjeta sólo vive el póster WebP: coste de red cero hasta que el
 * visitante decide ver. El `<video>` no existe en el DOM hasta que se abre el
 * lightbox, así que `preload="none"` no es una promesa, es un hecho.
 */
export function ProjectVideo({ media, title, locale, className = '' }: ProjectVideoProps) {
  const c = copy(locale);
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);

  const close = () => {
    setOpen(false);
    // El foco vuelve al disparador: quien abrió con teclado no se queda perdido.
    trigger.current?.focus();
  };

  const seconds = media.durationSeconds ? Math.round(media.durationSeconds) : null;

  // WCAG 2.5.3 (Label in Name): el nombre accesible tiene que *empezar* por el
  // texto visible del botón —duración incluida— o quien usa control por voz dice
  // lo que lee y no activa nada. De aquí sale el rótulo y la etiqueta, una sola
  // cadena, para que no puedan separarse otra vez.
  const label = `${c.microcopy.buttons.play_video}${seconds ? ` · ${seconds}s` : ''}`;

  return (
    <>
      <button
        ref={trigger}
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-label={`${label}: ${title}`}
        className={`group relative block w-full overflow-hidden border filete bg-surface-sunken ${className}`}
      >
        {media.poster ? (
          // El póster es la única imagen que se descarga hasta que alguien pulsa
          // play; `next/image` la sirve al ancho real del hueco en vez de a 1080p.
          <Image
            src={media.poster}
            alt=""
            width={media.width ?? 1920}
            height={media.height ?? 1080}
            sizes="(min-width: 1280px) 33vw, (min-width: 640px) 50vw, 100vw"
            className="block h-full w-full object-cover transition-transform duration-500 ease-cota group-hover:scale-[1.02]"
          />
        ) : (
          <span className="block aspect-video w-full" />
        )}

        <span className="pointer-events-none absolute inset-0 bg-prussian/0 transition-colors duration-300 group-hover:bg-prussian/15" />
        <CornerTicks size={12} className="text-paper opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

        <span className="pointer-events-none absolute bottom-0 left-0 flex items-center gap-2 bg-surface px-2 py-1">
          <span aria-hidden="true" className="block h-0 w-0 border-y-[5px] border-l-[8px] border-y-transparent border-l-accent" />
          <Annotation>{label}</Annotation>
        </span>
      </button>

      {open ? (
        <VideoLightbox media={media} title={title} locale={locale} onClose={close} />
      ) : null}
    </>
  );
}

export default ProjectVideo;
