import type { Metadata } from 'next';

import { fontVariables } from '@/lib/fonts';
import '@/styles/globals.css';

/**
 * Layout raíz del panel, aislado del público a propósito: aquí no hay GridOverlay,
 * ni Lenis, ni GSAP. Hereda los tokens del sistema de diseño y nada más — esto es
 * una herramienta de trabajo, y la densidad y la velocidad ganan al espectáculo.
 */
export const metadata: Metadata = {
  title: 'Panel · Félix Ruiz M.',
  robots: { index: false, follow: false },
};

export default function AdminRootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={`${fontVariables} min-h-screen bg-surface text-content antialiased`}>
        {children}
      </body>
    </html>
  );
}
