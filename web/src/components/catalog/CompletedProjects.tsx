import Link from 'next/link';

import Reveal from '@/components/motion/Reveal';
import ProjectShot from '@/components/media/ProjectShot';
import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import { isSheet } from '@/lib/api/sheets';
import type { Project } from '@/lib/api/types';
import { copy } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';
import { projectRoute } from '@/lib/routes';

interface CompletedProjectsProps {
  projects: Project[];
  locale: Locale;
}

/**
 * Proyectos BIM realizados: edificios con juego de planos, no herramientas.
 * Van aparte y en grande porque lo que se enseña es el dibujo, y en la tarjeta
 * de la rejilla una lámina no se lee.
 */
export function CompletedProjects({ projects, locale }: CompletedProjectsProps) {
  if (projects.length === 0) return null;
  const c = copy(locale);
  const text = c.areas.civil_bim.completed;

  return (
    <section aria-labelledby="realizados" className="mb-16">
      <header className="mb-8 flex flex-col gap-3 border-b filete pb-6">
        <Annotation leader>
          C · {projects.length} {text.count}
        </Annotation>
        <h2 id="realizados" className="font-display text-display-sm font-semibold text-content">
          {text.heading}
        </h2>
        <p className="max-w-prose text-base leading-relaxed text-muted">{text.intro}</p>
      </header>

      <Reveal stagger="[data-obra]" className="flex flex-col gap-gutter">
        {projects.map((project) => {
          const title = localize(project.title, locale);
          const href = projectRoute(project.slug, locale);
          const sheets = project.media.filter(isSheet).length;
          const cover = project.thumbnail ?? project.media.find((m) => m.kind === 'image')?.src ?? null;

          return (
            <article
              key={project.slug}
              data-obra
              className="group relative grid gap-6 border filete bg-surface p-4 transition-colors duration-300 hover:border-content/40 md:grid-cols-[1.35fr_1fr] md:p-6"
            >
              <CornerTicks size={10} className="text-accent" />
              <Link href={href} tabIndex={-1} aria-hidden="true" className="block">
                {cover ? (
                  <ProjectShot
                    media={{ src: cover, video: null, width: null, height: null }}
                    alt=""
                    ratio="16 / 10"
                    fit="contain"
                    sizes="(min-width: 768px) 55vw, 100vw"
                    className="bg-white"
                  />
                ) : null}
              </Link>

              <div className="flex flex-col gap-4 md:py-2">
                {sheets > 0 ? (
                  <Annotation accent>
                    {sheets} {text.sheets}
                  </Annotation>
                ) : null}
                <h3 className="font-display text-xl font-semibold text-content md:text-2xl">
                  <Link href={href} className="transition-colors duration-200 hover:text-accent-text">
                    {title}
                  </Link>
                </h3>
                <p className="text-base leading-relaxed text-muted">
                  {localize(project.summary, locale)}
                </p>
                <ul className="flex flex-wrap gap-x-3 gap-y-1">
                  {project.technologies.slice(0, 5).map((tech) => (
                    <li key={tech}>
                      <Annotation className="!normal-case">{tech}</Annotation>
                    </li>
                  ))}
                </ul>
                <Link
                  href={href}
                  className="mt-auto inline-flex items-center gap-2 font-mono text-note uppercase tracking-[0.14em] text-content transition-colors duration-200 hover:text-accent-text"
                >
                  {text.view} <span aria-hidden="true">→</span>
                </Link>
              </div>
            </article>
          );
        })}
      </Reveal>
    </section>
  );
}

export default CompletedProjects;
