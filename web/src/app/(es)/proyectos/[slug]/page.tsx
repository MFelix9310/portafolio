import type { Metadata } from 'next';

import ProjectView from '@/components/pages/ProjectView';
import { getProject, getProjectSlugs } from '@/lib/api/catalog';
import { t as localize } from '@/lib/i18n/locale';

export const revalidate = 300;

/** Pre-render de los slugs conocidos en build; el resto llega por ISR. */
export async function generateStaticParams() {
  const slugs = await getProjectSlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = await getProject(slug);
  if (!project) return { title: 'Proyecto no encontrado' };
  return {
    title: localize(project.title, 'es'),
    description: localize(project.summary, 'es').slice(0, 180),
  };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ProjectView slug={slug} locale="es" />;
}
