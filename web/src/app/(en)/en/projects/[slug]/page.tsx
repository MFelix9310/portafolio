import type { Metadata } from 'next';

import ProjectView from '@/components/pages/ProjectView';
import { getProject, getProjectSlugs } from '@/lib/api/catalog';
import { t as localize } from '@/lib/i18n/locale';

export const revalidate = 300;

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
  if (!project) return { title: 'Project not found' };
  return {
    title: localize(project.title, 'en'),
    description: localize(project.summary, 'en').slice(0, 180),
  };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <ProjectView slug={slug} locale="en" />;
}
