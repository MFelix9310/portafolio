import type { Metadata } from 'next';

import SiteShell from '@/components/layout/SiteShell';
import { SITE_NAME, SITE_URL } from '@/lib/site';
import '@/styles/globals.css';

const TITLE = 'Félix Ruiz M. — Portfolio';
const DESCRIPTION =
  'Civil engineer who builds engineering software. Structural calculation, BIM ' +
  'automation and data pipelines, with construction judgement inside the code.';

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: '%s · Félix Ruiz M.' },
  description: DESCRIPTION,
  applicationName: SITE_NAME,
  authors: [{ name: SITE_NAME }],
  alternates: {
    canonical: '/en',
    languages: { 'es-ES': '/', 'en-US': '/en', 'x-default': '/' },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    alternateLocale: ['es_ES'],
    url: '/en',
    siteName: SITE_NAME,
    title: TITLE,
    description: DESCRIPTION,
  },
  twitter: { card: 'summary_large_image', title: TITLE, description: DESCRIPTION },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <SiteShell locale="en">{children}</SiteShell>
    </html>
  );
}
