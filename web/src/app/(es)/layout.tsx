import type { Metadata } from 'next';

import SiteShell from '@/components/layout/SiteShell';
import { SITE_NAME, SITE_URL } from '@/lib/site';
import '@/styles/globals.css';

const TITULO = 'Félix Ruiz M. · Portafolio';
const DESCRIPCION =
  'Ingeniero civil que construye software de ingeniería. Cálculo estructural, ' +
  'automatización BIM y pipelines de datos, con el criterio de obra dentro del código.';

export const metadata: Metadata = {
  // Sin `metadataBase` correcto, las URL de Open Graph se resuelven contra un
  // host inexistente y la previsualizacion al compartir sale vacia.
  metadataBase: new URL(SITE_URL),
  title: { default: TITULO, template: '%s · Félix Ruiz M.' },
  description: DESCRIPCION,
  applicationName: SITE_NAME,
  authors: [{ name: SITE_NAME }],
  alternates: {
    canonical: '/',
    languages: { 'es-ES': '/', 'en-US': '/en', 'x-default': '/' },
  },
  openGraph: {
    type: 'website',
    locale: 'es_ES',
    alternateLocale: ['en_US'],
    url: '/',
    siteName: SITE_NAME,
    title: TITULO,
    description: DESCRIPCION,
  },
  twitter: { card: 'summary_large_image', title: TITULO, description: DESCRIPCION },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <SiteShell locale="es">{children}</SiteShell>
    </html>
  );
}
