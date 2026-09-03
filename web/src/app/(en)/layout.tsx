import type { Metadata } from 'next';

import SiteShell from '@/components/layout/SiteShell';
import '@/styles/globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://felixruiz.dev'),
  title: {
    default: "Félix Ruiz M. — Portfolio",
    template: '%s · Félix Ruiz M.',
  },
  description: "A drawing without dimensions is an illustration. With dimensions it is data. Portfolio of data, software and civil engineering by Félix Ruiz M.",
  alternates: { languages: { es: '/', en: '/en' } },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <SiteShell locale="en">{children}</SiteShell>
    </html>
  );
}
