import Image from 'next/image';

import AnimatedShot from './AnimatedShot';
import type { ProjectMedia } from '@/lib/api/types';

interface ProjectShotProps {
  media: Pick<ProjectMedia, 'src' | 'video' | 'width' | 'height'>;
  alt: string;
  /**
   * Proporción de reserva **cuando la media no trae ancho y alto**. Si los trae,
   * manda la proporción real y esto no se usa.
   */
  ratio?: string;
  /** `sizes` de `next/image`; describe el ancho real del hueco en cada breakpoint. */
  sizes: string;
  /**
   * `contain` en la galería —son planos y gráficas, recortarlos pierde datos— y
   * `cover` en las miniaturas de la rejilla, donde manda la regularidad.
   */
  fit?: 'contain' | 'cover';
  className?: string;
}

/**
 * Una imagen de proyecto dentro de un hueco de tamaño conocido.
 *
 * Resuelve dos cosas que antes estaban rotas:
 *
 * 1. **Saltos de maquetación.** El contenedor declara `aspect-ratio`, así que el
 *    hueco existe antes de que llegue el primer byte. Cuando la fila trae ancho
 *    y alto —hoy sólo los vídeos; la API tiene las columnas pero las imágenes
 *    vienen a `null`— se usa la proporción real y el ajuste es exacto. Cuando no,
 *    se reserva una proporción fija.
 *
 *    Se midieron las 47 imágenes de galería del catálogo: van de 0,86 a 5,18 de
 *    proporción, mediana 1,93. No hay un valor que le venga bien a todas, así que
 *    el fijo es 16/9 —por debajo de la mediana, que es donde menos hueco se
 *    desperdicia— con `object-contain` sobre el fondo hundido: nada se recorta,
 *    que estos son planos y gráficas. **No** se generan las dimensiones leyendo
 *    `public/media` porque ese directorio está en .gitignore y en producción la
 *    media la sirve Supabase Storage: el sitio correcto para esos dos números es
 *    `content/media-manifest.json` y la fila de `project_media`. En cuanto
 *    estén, este componente ya los usa sin tocar una línea.
 *
 * 2. **Los GIF.** Doce animaciones de gemelos digitales y campos de esfuerzos
 *    pesan 37 MB en WebP animado y 2,17 MB en la rendition H.264. Cuando existe
 *    `media.video` la pinta `AnimatedShot`, que reproduce el MP4 en bucle sin
 *    JavaScript. El porqué de no dejar el WebP de alternativa está allí.
 */
export function ProjectShot({
  media,
  alt,
  ratio = '16 / 9',
  sizes,
  fit = 'contain',
  className = '',
}: ProjectShotProps) {
  const object = fit === 'cover' ? 'object-cover' : 'object-contain';
  const intrinsic = media.width && media.height ? `${media.width} / ${media.height}` : null;

  return (
    <div
      className={`relative w-full overflow-hidden bg-surface-sunken ${className}`}
      style={{ aspectRatio: intrinsic ?? ratio }}
    >
      {media.video ? (
        <AnimatedShot video={media.video} alt={alt} object={object} />
      ) : (
        <Image
          src={media.src}
          alt={alt}
          fill
          sizes={sizes}
          // Ni galería ni rejilla asoman por encima del pliegue en ninguna ruta
          // —el LCP de las cuatro medidas es texto—, así que nada de `priority`:
          // precargar una imagen que no es el LCP sólo le quita ancho de banda.
          loading="lazy"
          className={object}
        />
      )}
    </div>
  );
}

export default ProjectShot;
