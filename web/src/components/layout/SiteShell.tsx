import type { ReactNode } from 'react';

import GridOverlay from '@/components/primitives/GridOverlay';
import SiteFooter from './SiteFooter';
import SiteHeader from './SiteHeader';
import SmoothScroll from '@/components/motion/SmoothScroll';
import { fontVariables } from '@/lib/fonts';
import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';

const THEME_SCRIPT = `try{var t=localStorage.getItem('cota-theme');if(t==='dark'||t==='light'){document.documentElement.setAttribute('data-theme',t)}}catch(e){}`;

/**
 * Lámina completa: retícula dibujada al fondo, cajetín arriba y abajo, y el
 * contenido apoyado encima. Se comparte entre los dos layouts raíz (ES y EN).
 */
export function SiteShell({
  locale,
  children,
}: {
  locale: Locale;
  children: ReactNode;
}) {
  return (
    <body className={`${fontVariables} min-h-screen bg-surface antialiased`}>
      {/* Aplica el tema guardado antes de pintar, para que no haya destello. */}
      <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      <a className="salto-contenido" href="#contenido">
        {copy(locale).chrome.skip_to_content}
      </a>
      <GridOverlay />
      <SmoothScroll />
      <div className="relative z-10 flex min-h-screen flex-col">
        <SiteHeader locale={locale} />
        <main id="contenido" className="flex-1">
          {children}
        </main>
        <SiteFooter locale={locale} />
      </div>
    </body>
  );
}

export default SiteShell;
