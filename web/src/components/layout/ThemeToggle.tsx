'use client';

import { useEffect, useState } from 'react';

import { copy } from '@/lib/i18n/copy';
import type { Locale } from '@/lib/i18n/locale';

type Theme = 'light' | 'dark' | 'system';

const ORDER: Theme[] = ['system', 'light', 'dark'];

/**
 * El modo oscuro es el cianotipo invertido. Por defecto manda el sistema
 * (`prefers-color-scheme`); este conmutador escribe `data-theme` y lo sobreescribe.
 */
export function ThemeToggle({ locale }: { locale: Locale }) {
  const labels = copy(locale).chrome.theme;
  const [theme, setTheme] = useState<Theme>('system');

  useEffect(() => {
    const stored = window.localStorage.getItem('cota-theme') as Theme | null;
    if (stored && ORDER.includes(stored)) setTheme(stored);
  }, []);

  const cycle = () => {
    const next = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length]!;
    setTheme(next);
    window.localStorage.setItem('cota-theme', next);
    if (next === 'system') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', next);
    }
  };

  return (
    <button
      type="button"
      onClick={cycle}
      className="border filete px-2 py-1 font-mono text-note uppercase tracking-[0.14em] text-muted transition-colors duration-200 hover:text-content"
      aria-label={labels.label}
    >
      {labels[theme]}
    </button>
  );
}

export default ThemeToggle;
