import Link from 'next/link';
import { notFound } from 'next/navigation';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import DetailEntrance from '@/components/motion/DetailEntrance';
import ProjectShot from '@/components/media/ProjectShot';
import ProjectVideo from '@/components/media/ProjectVideo';
import Reveal from '@/components/motion/Reveal';
import { getProject } from '@/lib/api/catalog';
import { areaName, subareaName } from '@/lib/api/taxonomy';
import { copy } from '@/lib/i18n/copy';
import { t as localize, type Locale } from '@/lib/i18n/locale';
import { route } from '@/lib/routes';

interface ProjectViewProps {
  slug: string;
  locale: Locale;
}

export async function ProjectView({ slug, locale }: ProjectViewProps) {
  const c = copy(locale);
  const project = await getProject(slug);
  if (!project) notFound();

  const title = localize(project.title, locale);
  const videos = project.media.filter((item) => item.kind === 'video');
  const images = project.media.filter((item) => item.kind === 'image');
  const documents = project.media.filter((item) => item.kind === 'document');
  const primaryArea = project.tags[0]?.area ?? 'data';

  return (
    <DetailEntrance>
      <article className="lamina py-10 md:py-14">
        <Link
          href={route(primaryArea, locale)}
          className="mb-8 inline-flex items-center gap-2 font-mono text-note uppercase tracking-[0.14em] text-muted transition-colors duration-200 hover:text-content"
        >
          <span aria-hidden="true">←</span> {c.microcopy.buttons.back} ·{' '}
          {localize(areaName(primaryArea), locale)}
        </Link>

        <header className="mb-10 grid gap-6 border-b filete pb-8 md:grid-cols-[1.6fr_1fr]">
          <div className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-x-4 gap-y-1">
              {project.tags.map((tag) => (
                <Annotation key={`${tag.area}-${tag.subarea}`} accent>
                  {localize(areaName(tag.area), locale)} /{' '}
                  {localize(subareaName(tag.area, tag.subarea), locale)}
                </Annotation>
              ))}
            </div>
            <h1 className="font-display text-display-sm font-semibold text-content">{title}</h1>
            <p className="max-w-prose text-base leading-relaxed text-muted md:text-lg">
              {localize(project.summary, locale)}
            </p>
          </div>

          <dl className="relative grid h-fit grid-cols-[auto_1fr] gap-x-4 gap-y-2 border filete p-4">
            <CornerTicks size={8} />
            <dt className="font-mono text-note uppercase tracking-[0.14em] text-faint">
              {c.chrome.project.technologies}
            </dt>
            <dd className="flex flex-wrap gap-x-3 gap-y-1">
              {project.technologies.map((tech) => (
                <span key={tech} className="font-mono text-note text-content">
                  {tech}
                </span>
              ))}
            </dd>
            {project.repositoryUrl || project.projectUrl ? (
              <>
                <dt className="font-mono text-note uppercase tracking-[0.14em] text-faint">
                  {c.chrome.project.links}
                </dt>
                <dd className="flex flex-col gap-1">
                  {project.repositoryUrl ? (
                    <a
                      href={project.repositoryUrl}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="font-mono text-note text-accent-text underline underline-offset-4"
                    >
                      {c.microcopy.buttons.view_repository}
                    </a>
                  ) : null}
                  {project.projectUrl ? (
                    <a
                      href={project.projectUrl}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="font-mono text-note text-accent-text underline underline-offset-4"
                    >
                      {c.microcopy.buttons.view_demo}
                    </a>
                  ) : null}
                </dd>
              </>
            ) : null}
          </dl>
        </header>

        {project.body ? (
          <div className="mb-12 max-w-prose whitespace-pre-line text-base leading-relaxed text-content">
            {localize(project.body, locale)}
          </div>
        ) : null}

        {videos.length > 0 ? (
          <section aria-labelledby="video" className="mb-14">
            <h2 id="video" className="mb-4 font-display text-xl font-semibold text-content">
              {c.chrome.project.video}
            </h2>
            <div className="grid gap-gutter md:grid-cols-2">
              {videos.map((media) => (
                <ProjectVideo key={media.id} media={media} title={title} locale={locale} />
              ))}
            </div>
          </section>
        ) : null}

        {images.length > 0 ? (
          <section aria-labelledby="imagenes" className="mb-14">
            <h2 id="imagenes" className="mb-4 font-display text-xl font-semibold text-content">
              {c.chrome.project.images}
            </h2>
            <Reveal stagger="[data-shot]" className="grid gap-gutter sm:grid-cols-2 lg:grid-cols-3">
              {images.map((media) => (
                <figure key={media.id} data-shot className="relative border filete bg-surface-sunken">
                  <CornerTicks size={8} />
                  <ProjectShot
                    media={media}
                    alt={media.caption ? localize(media.caption, locale) : ''}
                    sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
                  />
                  {media.caption ? (
                    <figcaption className="border-t filete px-3 py-2">
                      <Annotation className="!normal-case">
                        {localize(media.caption, locale)}
                      </Annotation>
                    </figcaption>
                  ) : null}
                </figure>
              ))}
            </Reveal>
          </section>
        ) : null}

        {documents.length > 0 ? (
          <section aria-labelledby="documentos">
            <h2 id="documentos" className="mb-4 font-display text-xl font-semibold text-content">
              {c.chrome.project.documents}
            </h2>
            <ul className="flex flex-col border-t filete">
              {documents.map((media) => (
                <li key={media.id}>
                  <a
                    href={media.src}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="flex items-center justify-between gap-4 border-b filete py-3 font-mono text-note uppercase tracking-[0.14em] text-content transition-colors duration-200 hover:text-accent-text"
                  >
                    <span>{media.title ? localize(media.title, locale) : media.src.split('/').pop()}</span>
                    <span aria-hidden="true">↗</span>
                  </a>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </article>
    </DetailEntrance>
  );
}

export default ProjectView;
