import type { ReactNode } from 'react';

interface AnimatedShotProps {
  /** Rendition H.264 de la animación. */
  video: string;
  alt: string;
  /** `object-contain` u `object-cover`, ya resuelto por quien llama. */
  object: string;
}

/**
 * Animación de proyecto: `<video>` en bucle, sin una línea de JavaScript.
 *
 * Las doce animaciones del catálogo pesan 37 MB en WebP animado y 2,17 MB en la
 * rendition H.264. Sustituirlas es la mayor palanca de red que quedaba, pero las
 * dos formas obvias de dejar el WebP como alternativa salen caras y se midieron
 * las dos:
 *
 * - **`<img>` dentro del `<video>`** (la forma declarativa). Chrome descarga el
 *   recurso de cualquier `<img>` conectado al documento aunque la alternativa no
 *   se pinte nunca —se comprobó con `naturalWidth` distinto de cero con el vídeo
 *   reproduciéndose—. Se pagaban los 201 kB del MP4 **y** los 5,9 MB del WebP:
 *   la optimización entera, anulada.
 * - **Componente cliente con `onError`.** Sin descarga de más, pero convierte
 *   cada animación en un límite de cliente. En la rejilla de `/civil-bim` son
 *   seis, y el tiempo de evaluación de script subió de 735 a 933 ms en el mismo
 *   informe de Lighthouse.
 *
 * Así que no hay alternativa: `<video>` y nada más. Lo que protegía era un
 * navegador sin H.264 en MP4, que es soporte universal desde hace más de una
 * década; el pie de figura sigue describiendo lo que se ve.
 */
export function AnimatedShot({ video, alt, object }: AnimatedShotProps): ReactNode {
  return (
    <video
      src={video}
      autoPlay
      loop
      muted
      playsInline
      // No `auto`: con `autoplay` el navegador ya decide cuándo traerse el resto
      // y aplaza las que están fuera de pantalla.
      preload="metadata"
      aria-label={alt || undefined}
      className={`absolute inset-0 h-full w-full ${object}`}
    />
  );
}

export default AnimatedShot;
