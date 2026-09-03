import type { Metadata } from 'next';

import SiteShell from '@/components/layout/SiteShell';
import '@/styles/globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://felixruiz.dev'),
  title: {
    default: "Félix Ruiz M. — Portafolio",
    template: '%s · Félix Ruiz M.',
  },
  description: "Un plano sin cotas es una ilustración. Con cotas es un dato. Portafolio de datos, desarrollo e ingeniería civil de Félix Ruiz M.",
  alternates: { languages: { es: '/', en: '/en' } },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <SiteShell locale="es">{children}</SiteShell>
    </html>
  );
}
