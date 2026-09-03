'use client';

import dynamic from 'next/dynamic';

import type { Locale } from '@/lib/i18n/locale';

/**
 * Hueco del gesto 4. Se carga con `ssr: false` para que el bloque 3D (cuando
 * exista) no entre en el bundle inicial ni se ejecute en servidor.
 */
const ExtrusionPlaceholder = dynamic(() => import('./ExtrusionPlaceholder'), {
  ssr: false,
  loading: () => <div className="aspect-[16/9] w-full border filete bg-surface-sunken" />,
});

export function ExtrusionSlot({ locale }: { locale: Locale }) {
  return <ExtrusionPlaceholder locale={locale} />;
}

export default ExtrusionSlot;
