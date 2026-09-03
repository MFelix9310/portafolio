'use client';

import { useEffect, useRef, useState } from 'react';

import ProjectCard from './ProjectCard';
import type { Project } from '@/lib/api/types';
import type { Locale } from '@/lib/i18n/locale';
import { DUR, EASE, ensureGsap, prefersReducedMotion } from '@/lib/motion';

interface ProjectGridProps {
  projects: Project[];
  locale: Locale;
}

const signatureOf = (projects: Project[]) => projects.map((project) => project.slug).join('|');

/**
 * Gesto 2 — capas CAD.
 *
 * Al apagar una capa, sus proyectos no desaparecen de golpe: primero se vacía el
 * contenido y queda el filete (el rectángulo de la capa oculta), y sólo después
 * se retira. Sólo se animan `opacity` y `transform`.
 */
export function ProjectGrid({ projects, locale }: ProjectGridProps) {
  const container = useRef<HTMLDivElement>(null);
  const [rendered, setRendered] = useState<Project[]>(projects);
  const previous = useRef<string>(signatureOf(projects));
  const firstRender = useRef(true);
  const signature = signatureOf(projects);

  useEffect(() => {
    if (previous.current === signature) return;

    const element = container.current;
    const nextSlugs = new Set(projects.map((project) => project.slug));
    const leaving = rendered.filter((project) => !nextSlugs.has(project.slug));

    if (!element || prefersReducedMotion() || leaving.length === 0) {
      previous.current = signature;
      setRendered(projects);
      return;
    }

    const gsap = ensureGsap();
    const slots = leaving
      .map((project) => element.querySelector<HTMLElement>(`[data-slot="${project.slug}"]`))
      .filter((node): node is HTMLElement => node !== null);

    if (slots.length === 0) {
      previous.current = signature;
      setRendered(projects);
      return;
    }

    const timeline = gsap.timeline({
      onComplete: () => {
        previous.current = signature;
        setRendered(projects);
      },
    });

    timeline
      .to(
        slots.map((slot) => slot.querySelector('[data-slot-body]')),
        { autoAlpha: 0, duration: DUR.layer, ease: EASE },
        0,
      )
      .to(
        slots.map((slot) => slot.querySelector('[data-slot-ghost]')),
        { autoAlpha: 1, duration: DUR.layer * 0.6, ease: EASE },
        0,
      )
      .to(slots, { autoAlpha: 0, scale: 0.99, duration: DUR.layer, ease: EASE }, DUR.layer * 0.9);

    return () => {
      timeline.kill();
    };
  }, [signature, projects, rendered]);

  // Los que entran vienen del estado "capa apagada": filete primero, contenido después.
  useEffect(() => {
    const element = container.current;
    if (!element) return;

    const fresh = element.querySelectorAll<HTMLElement>('[data-slot][data-fresh="true"]');
    fresh.forEach((slot) => slot.setAttribute('data-fresh', 'false'));

    // En el primer montaje no hay "entrada": las tarjetas ya están dibujadas.
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    if (prefersReducedMotion() || fresh.length === 0) return;

    const gsap = ensureGsap();
    gsap.fromTo(
      fresh,
      { autoAlpha: 0, y: 12 },
      { autoAlpha: 1, y: 0, duration: DUR.layer, ease: EASE, stagger: 0.05 },
    );
  }, [rendered]);

  return (
    <div
      ref={container}
      className="grid grid-cols-1 gap-gutter sm:grid-cols-2 xl:grid-cols-3"
    >
      {rendered.map((project) => (
        <div key={project.slug} data-slot={project.slug} data-fresh="true" className="relative">
          <span
            data-slot-ghost
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 border filete opacity-0"
          />
          <div data-slot-body className="h-full">
            <ProjectCard project={project} locale={locale} />
          </div>
        </div>
      ))}
    </div>
  );
}

export default ProjectGrid;
