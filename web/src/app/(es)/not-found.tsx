import Link from 'next/link';

import Annotation from '@/components/primitives/Annotation';
import CornerTicks from '@/components/primitives/CornerTicks';
import { copy } from '@/lib/i18n/copy';

export default function NotFound() {
  const notFound = copy('es').chrome.not_found;

  return (
    <div className="lamina flex min-h-[60vh] items-center py-16">
      <div className="relative border filete p-8 md:p-12">
        <CornerTicks size={14} />
        <Annotation leader accent className="mb-4">
          {notFound.eyebrow}
        </Annotation>
        <h1 className="mb-4 font-display text-display-sm font-semibold text-content">
          {notFound.title}
        </h1>
        <p className="mb-6 max-w-prose text-base leading-relaxed text-muted">{notFound.body}</p>
        <Link
          href="/"
          className="border filete px-3 py-2 font-mono text-note uppercase tracking-[0.14em] text-content transition-colors duration-200 hover:bg-content hover:text-surface"
        >
          {notFound.back}
        </Link>
      </div>
    </div>
  );
}
