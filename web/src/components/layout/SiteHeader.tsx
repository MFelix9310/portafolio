'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import ThemeToggle from './ThemeToggle';
import { areaCopyKey, copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';
import { route, swapLocale, type RouteKey } from '@/lib/routes';

const LINKS: RouteKey[] = ['data', 'developer', 'civil-bim', 'about', 'contact'];

/** Una sola fuente para el cajetín: lo que se lee y lo que se anuncia no pueden separarse. */
const WORDMARK = { initials: 'FRM', name: 'Félix Ruiz M.' } as const;

/** Cajetín superior de la lámina: identidad a la izquierda, índice a la derecha. */
export function SiteHeader({ locale }: { locale: Locale }) {
  const c = copy(locale);
  const label = (key: RouteKey) =>
    key === 'about' || key === 'contact' || key === 'home'
      ? c.nav[key]
      : c.nav.areas[areaCopyKey(key)];
  const pathname = usePathname() ?? '/';
  const [open, setOpen] = useState(false);

  const isActive = (key: RouteKey) => pathname === route(key, locale);

  return (
    <header className="relative z-30 border-b filete bg-surface/85 backdrop-blur-sm">
      <div className="lamina flex h-14 items-center justify-between gap-4">
        {/* WCAG 2.5.3: la etiqueta tiene que *contener* el texto visible del
            cajetín, no sustituirlo, o el control por voz no encuentra el enlace. */}
        <Link
          href={route('home', locale)}
          className="group flex items-baseline gap-2"
          aria-label={`${WORDMARK.initials} ${WORDMARK.name} — ${c.nav.home}`}
        >
          <span className="text-cajetin text-sm font-semibold text-content">
            {WORDMARK.initials}
          </span>
          <span className="hidden font-mono text-note text-muted sm:inline">{WORDMARK.name}</span>
        </Link>

        <nav aria-label={c.chrome.menu.label} className="hidden items-center gap-6 md:flex">
          {LINKS.map((key) => (
            <Link
              key={key}
              href={route(key, locale)}
              aria-current={isActive(key) ? 'page' : undefined}
              className={`relative font-mono text-note uppercase tracking-[0.14em] transition-colors duration-200 ${
                isActive(key) ? 'text-content' : 'text-muted hover:text-content'
              }`}
            >
              {label(key)}
              {isActive(key) ? (
                <span aria-hidden="true" className="absolute -bottom-1.5 left-0 h-px w-full bg-accent" />
              ) : null}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <div
            className="flex items-center border filete"
            role="group"
            aria-label={c.chrome.language_label}
          >
            {(['es', 'en'] as const).map((code) => (
              <Link
                key={code}
                href={swapLocale(pathname, code)}
                hrefLang={code}
                aria-current={locale === code ? 'true' : undefined}
                className={`px-2 py-1 font-mono text-note uppercase tracking-[0.14em] transition-colors duration-200 ${
                  locale === code
                    ? 'bg-content text-surface'
                    : 'text-muted hover:text-content'
                }`}
              >
                {code}
              </Link>
            ))}
          </div>

          <ThemeToggle locale={locale} />

          <button
            type="button"
            className="border filete px-2 py-1 font-mono text-note uppercase tracking-[0.14em] text-muted md:hidden"
            aria-expanded={open}
            aria-controls="menu-movil"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? c.chrome.menu.close : c.chrome.menu.open}
          </button>
        </div>
      </div>

      {open ? (
        <nav
          id="menu-movil"
          aria-label={c.chrome.menu.label}
          className="border-t filete bg-surface md:hidden"
        >
          <ul className="lamina flex flex-col py-2">
            {LINKS.map((key) => (
              <li key={key}>
                <Link
                  href={route(key, locale)}
                  onClick={() => setOpen(false)}
                  aria-current={isActive(key) ? 'page' : undefined}
                  className="block py-2 font-mono text-note-lg uppercase tracking-[0.14em] text-content"
                >
                  {label(key)}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
    </header>
  );
}

export default SiteHeader;
