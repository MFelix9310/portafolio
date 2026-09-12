'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRef, type MouseEvent } from 'react';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import ProjectShot from '@/components/media/ProjectShot';
import ProjectVideo from '@/components/media/ProjectVideo';
import { subareaName } from '@/lib/api/taxonomy';
import type { Project } from '@/lib/api/types';
import { t as localize, type Locale } from '@/lib/i18n/locale';
import { ensureGsap, prefersReducedMotion } from '@/lib/motion';
import { projectRoute } from '@/lib/routes';

interface ProjectCardProps {
  project: Project;
  locale: Locale;
}

/**
 * Tarjeta de proyecto. El clic en el título dispara el gesto 3: una marca de
 * sección se dibuja sobre la tarjeta antes de navegar, de modo que el detalle
 * parece crecer del despiece y no aparecer de la nada.
 */
export function ProjectCard({ project, locale }: ProjectCardProps) {
  const router = useRouter();
  const card = useRef<HTMLElement>(null);
  const href = projectRoute(project.slug, locale);

  const title = localize(project.title, locale);
  const video = project.media.find((item) => item.kind === 'video');
  const image = project.media.find((item) => item.kind === 'image');
  // Si la portada es un GIF, la rejilla del área servía entre 1,6 y 3 MB por
  // tarjeta. La rendition H.264 es la misma animación con un orden de magnitud
  // menos; `ProjectShot` deja el WebP de alternativa dentro del propio <video>.
  const cover = project.thumbnail ?? image?.src ?? null;
  const coverVideo = project.thumbnail ? project.thumbnailVideo : (image?.video ?? null);

  const openDetail = (event: MouseEvent<HTMLAnchorElement>) => {
    if (prefersReducedMotion() || event.metaKey || event.ctrlKey || event.shiftKey) return;
    const element = card.current;
    if (!element) return;

    event.preventDefault();
    const gsap = ensureGsap();
    gsap
      .timeline({ onComplete: () => router.push(href) })
      .set(element.querySelectorAll('[data-mark]'), { autoAlpha: 1 })
      .fromTo(
        element.querySelectorAll('[data-mark-h]'),
        { scaleX: 0 },
        { scaleX: 1, duration: 0.24, ease: 'power2.inOut' },
        0,
      )
      .fromTo(
        element.querySelectorAll('[data-mark-v]'),
        { scaleY: 0 },
        { scaleY: 1, duration: 0.24, ease: 'power2.inOut' },
        0.05,
      )
      .to(element, { scale: 1.012, duration: 0.2, ease: 'power2.out' }, 0.1);
  };

  return (
    <article
      ref={card}
      data-project={project.slug}
      className="group relative flex flex-col border filete bg-surface p-4 transition-colors duration-300 hover:border-content/40"
    >
      <CornerTicks size={10} className="text-content opacity-0 transition-opacity duration-300 group-hover:opacity-70" />

      {/* Marca de sección del gesto 3: invisible hasta que se abre el detalle. */}
      <span aria-hidden="true" className="pointer-events-none absolute inset-0 z-10">
        <span data-mark data-mark-h className="absolute left-0 top-1/2 h-px w-full origin-left bg-accent opacity-0" />
        <span data-mark data-mark-v className="absolute left-1/2 top-0 h-full w-px origin-top bg-accent opacity-0" />
      </span>

      <div className="relative mb-4 aspect-video w-full overflow-hidden bg-surface-sunken">
        {video ? (
          <ProjectVideo media={video} title={title} locale={locale} className="h-full" />
        ) : cover ? (
          <ProjectShot
            media={{ src: cover, video: coverVideo, width: null, height: null }}
            alt=""
            ratio="16 / 9"
            fit="cover"
            sizes="(min-width: 1280px) 33vw, (min-width: 640px) 50vw, 100vw"
            className="h-full"
          />
        ) : (
          <span className="flex h-full w-full items-center justify-center">
            <Annotation>s/i</Annotation>
          </span>
        )}
      </div>

      <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1">
        {project.tags.map((tag) => (
          <Annotation key={`${tag.area}-${tag.subarea}`}>
            {localize(subareaName(tag.area, tag.subarea), locale)}
          </Annotation>
        ))}
      </div>

      {/* `h2`, no `h3`: el `h1` de la página es el nombre del área y la rejilla
          cuelga directamente de él. Saltarse el escalón rompe la navegación por
          encabezados y deja al rastreador sin la jerarquía del índice. */}
      <h2 className="mb-2 font-display text-xl font-semibold leading-tight tracking-tight text-content">
        <Link href={href} onClick={openDetail} className="underline-offset-4 hover:underline">
          {title}
        </Link>
      </h2>

      <p className="mb-4 line-clamp-3 text-sm leading-relaxed text-muted">
        {localize(project.summary, locale)}
      </p>

      <div className="mt-auto flex flex-wrap gap-x-3 gap-y-1 border-t filete pt-3">
        {project.technologies.slice(0, 4).map((tech) => (
          <Annotation key={tech} className="!normal-case !tracking-[0.08em]">
            {tech}
          </Annotation>
        ))}
        {project.technologies.length > 4 ? (
          <Annotation accent>+{project.technologies.length - 4}</Annotation>
        ) : null}
      </div>
    </article>
  );
}

export default ProjectCard;
