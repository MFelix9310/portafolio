'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

import ProjectCard from './ProjectCard';
import { useLayers } from './LayerState';
import type { AreaKey, Project } from '@/lib/api/types';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';
import { DUR, EASE, ensureGsap, prefersReducedMotion } from '@/lib/motion';

interface ProjectGridProps {
  projects: Project[];
  areaKey: AreaKey;
  locale: Locale;
}

interface Pending {
  /** Capas apagadas que hay que confirmar cuando acabe la animación. */
  hidden: string[];
  entering: string[];
  leaving: string[];
}

/**
 * Gesto 2 — capas CAD.
 *
 * La rejilla la dibuja el servidor con **todos** los proyectos del área, porque
 * ése es el estado por defecto y así las tarjetas existen en el HTML servido
 * (indexación, previsualizaciones al compartir, rastreadores). Sin JavaScript se
 * ven todos: la degradación correcta.
 *
 * El cliente sólo *oculta*. Y lo hace por `className`, que es de React, no
 * escribiendo `style.display` a mano: en un rerender React no tiene nada que
 * deshacer. GSAP se queda con `opacity` y `transform`, que nadie más toca.
 *
 * Al apagar una capa, sus proyectos no desaparecen de golpe: primero se vacía el
 * contenido y queda el filete (el rectángulo de la capa oculta), y sólo después
 * se retira de la lámina.
 */
export function ProjectGrid({ projects, areaKey, locale }: ProjectGridProps) {
  const c = copy(locale);
  const container = useRef<HTMLDivElement>(null);
  const { active, animate } = useLayers();

  // Estado confirmado. Arranca vacío para que el cliente hidrate exactamente el
  // HTML que sirvió el servidor: nada oculto.
  const [hidden, setHidden] = useState<string[]>([]);
  const [pending, setPending] = useState<Pending | null>(null);

  /** Última selección pedida, ya confirmada o aún animándose. */
  const requested = useRef<string[]>([]);

  const subareasOf = (project: Project) =>
    project.tags.filter((tag) => tag.area === areaKey).map((tag) => tag.subarea);

  const target = useMemo(() => {
    if (active === null) return [] as string[];
    return projects
      .filter((project) => !subareasOf(project).some((subarea) => active.includes(subarea)))
      .map((project) => project.slug);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, projects, areaKey]);

  const targetKey = target.join('|');

  useEffect(() => {
    // El montaje y los rerenders que no mueven la selección no tocan nada: el
    // HTML servido ya es el estado correcto.
    if (requested.current.join('|') === targetKey) return;

    const before = new Set(requested.current);
    const after = new Set(target);
    const slugs = projects.map((project) => project.slug);
    const entering = slugs.filter((slug) => before.has(slug) && !after.has(slug));
    const leaving = slugs.filter((slug) => !before.has(slug) && after.has(slug));

    requested.current = target;

    const element = container.current;
    const node = (slug: string) =>
      element?.querySelector<HTMLElement>(`[data-slot="${slug}"]`) ?? null;

    // Selección que venía en la URL al cargar, o movimiento reducido: se
    // confirma seca. Se limpian los estilos en línea que pudiera haber dejado
    // GSAP para que nada reaparezca transparente.
    if (!animate || prefersReducedMotion() || (entering.length === 0 && leaving.length === 0)) {
      const reset = entering.map(node).filter((item): item is HTMLElement => item !== null);
      if (reset.length > 0) {
        ensureGsap().set([...reset, ...parts(reset)], { clearProps: 'all' });
      }
      setHidden(target);
      return;
    }

    // Fase 1: los que entran ya se dibujan, los que salen siguen en la lámina
    // mientras se animan. Fase 2 (efecto de abajo) confirma el estado final.
    setHidden(slugs.filter((slug) => before.has(slug) && after.has(slug)));
    setPending({ hidden: target, entering, leaving });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetKey, animate]);

  useEffect(() => {
    if (pending === null) return;

    const element = container.current;
    const commit = () => {
      setHidden(pending.hidden);
      setPending(null);
    };

    if (!element) {
      commit();
      return;
    }

    const gsap = ensureGsap();
    const nodes = (slugs: string[]) =>
      slugs
        .map((slug) => element.querySelector<HTMLElement>(`[data-slot="${slug}"]`))
        .filter((item): item is HTMLElement => item !== null);

    // Los que entran vienen del estado "capa apagada": filete primero, contenido
    // después. `clearProps` borra lo que dejó la salida anterior.
    const enter = nodes(pending.entering);
    if (enter.length > 0) {
      gsap.set([...enter, ...parts(enter)], { clearProps: 'all' });
      gsap.fromTo(
        enter,
        { autoAlpha: 0, y: 12 },
        { autoAlpha: 1, y: 0, duration: DUR.layer, ease: EASE, stagger: 0.05 },
      );
    }

    const leave = nodes(pending.leaving);
    if (leave.length === 0) {
      commit();
      return;
    }

    const timeline = gsap.timeline({ onComplete: commit });
    timeline
      .to(
        leave.map((slot) => slot.querySelector('[data-slot-body]')),
        { autoAlpha: 0, duration: DUR.layer, ease: EASE },
        0,
      )
      .to(
        leave.map((slot) => slot.querySelector('[data-slot-ghost]')),
        { autoAlpha: 1, duration: DUR.layer * 0.6, ease: EASE },
        0,
      )
      .to(leave, { autoAlpha: 0, scale: 0.99, duration: DUR.layer, ease: EASE }, DUR.layer * 0.9);

    return () => {
      timeline.kill();
    };
  }, [pending]);

  const off = new Set(hidden);
  const allOff = projects.length > 0 && off.size === projects.length;

  return (
    <>
      <div ref={container} className="grid grid-cols-1 gap-gutter sm:grid-cols-2 xl:grid-cols-3">
        {projects.map((project) => (
          <div
            key={project.slug}
            data-slot={project.slug}
            data-subarea={subareasOf(project).join(' ')}
            className={off.has(project.slug) ? 'relative hidden' : 'relative'}
          >
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

      {allOff ? (
        <p className="border filete p-8 text-center font-mono text-note uppercase tracking-[0.14em] text-muted">
          {c.chrome.layers.all_off}
        </p>
      ) : null}
    </>
  );
}

/** Cuerpo y filete de cada hueco: lo que anima la transición de capa. */
function parts(slots: HTMLElement[]): HTMLElement[] {
  return slots.flatMap((slot) =>
    [
      slot.querySelector<HTMLElement>('[data-slot-body]'),
      slot.querySelector<HTMLElement>('[data-slot-ghost]'),
    ].filter((item): item is HTMLElement => item !== null),
  );
}

export default ProjectGrid;
