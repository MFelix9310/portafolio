import Link from 'next/link';

import Annotation from '@/components/primitives/Annotation';
import SheetNumber from './SheetNumber';
import { copy, withYear } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';
import { route } from '@/lib/routes';
import { getCatalog } from '@/lib/api/catalog';

/**
 * El cajetín de la lámina. Lleva lo que lleva un cajetín real: quién firma, qué
 * lámina es, a qué escala y de dónde salen los datos.
 */
export async function SiteFooter({ locale }: { locale: Locale }) {
  const c = copy(locale);
  const catalog = await getCatalog();

  return (
    <footer className="relative z-10 mt-24 border-t filete bg-surface">
      <div className="lamina grid gap-8 py-10 md:grid-cols-[2fr_1fr_1fr]">
        <div className="flex flex-col gap-3">
          <span className="text-cajetin text-lg font-semibold text-content">
            Félix Ruiz M.
          </span>
          {/* La frase de posicionamiento, no la lista de títulos del sitio viejo. */}
          <p className="max-w-prose text-sm leading-relaxed text-muted">
            {c.microcopy.footer.tagline}
          </p>
          <Annotation as="p">
            {withYear(c.microcopy.footer.copyright, new Date().getFullYear())}
          </Annotation>
        </div>

        <div className="flex flex-col gap-2">
          <Annotation leader>{c.chrome.contact_channels}</Annotation>
          <ul className="flex flex-col gap-1">
            {catalog.contacts.map((contact) => (
              <li key={contact.kind}>
                <a
                  href={contact.value}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="font-mono text-note uppercase tracking-[0.14em] text-muted underline-offset-4 transition-colors duration-200 hover:text-content hover:underline"
                >
                  {c.contact.channels[contact.kind] ?? contact.kind}
                </a>
              </li>
            ))}
            <li>
              <Link
                href={route('contact', locale)}
                className="font-mono text-note uppercase tracking-[0.14em] text-muted underline-offset-4 transition-colors duration-200 hover:text-content hover:underline"
              >
                {c.nav.contact}
              </Link>
            </li>
          </ul>
        </div>

        {/* Cuadro de rotulación: los metadatos de la lámina, en mono. */}
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 self-start border filete p-3">
          <dt className="font-mono text-note uppercase tracking-[0.14em] text-faint">
            {c.chrome.sheet.label}
          </dt>
          <dd className="font-mono text-note tabular-nums text-content">
            <SheetNumber />
          </dd>
          <dt className="font-mono text-note uppercase tracking-[0.14em] text-faint">
            {c.chrome.sheet.scale}
          </dt>
          <dd className="font-mono text-note tabular-nums text-content">1:1</dd>
          <dt className="font-mono text-note uppercase tracking-[0.14em] text-faint">
            {c.chrome.sheet.source}
          </dt>
          <dd className="font-mono text-note text-content">
            {catalog.source === 'api' ? c.chrome.sheet.source_api : c.chrome.sheet.source_seed}
          </dd>
        </dl>
      </div>
    </footer>
  );
}

export default SiteFooter;
