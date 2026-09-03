import type { Config } from 'tailwindcss';

/** `rgb(var(--x) / <alpha>)` permite `text-ink/60` sobre variables CSS. */
const token = (name: string) => `rgb(var(${name}) / <alpha-value>)`;

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    // Esquinas vivas por defecto y por decreto: si alguien escribe `rounded-lg`,
    // no pasa nada, porque todos los radios valen 0. Donde haría falta suavizar
    // se usa <CornerTicks />.
    borderRadius: {
      none: '0',
      DEFAULT: '0',
      sm: '0',
      md: '0',
      lg: '0',
      xl: '0',
      '2xl': '0',
      '3xl': '0',
      full: '0',
    },
    extend: {
      colors: {
        paper: token('--paper'),
        ink: token('--ink'),
        prussian: token('--prussian'),
        revision: token('--revision'),
        graphite: {
          100: token('--graphite-100'),
          200: token('--graphite-200'),
          300: token('--graphite-300'),
          400: token('--graphite-400'),
          500: token('--graphite-500'),
          600: token('--graphite-600'),
        },
        surface: token('--surface'),
        'surface-sunken': token('--surface-sunken'),
        'surface-inverted': token('--surface-inverted'),
        content: token('--text'),
        muted: token('--text-muted'),
        faint: token('--text-faint'),
        'on-inverted': token('--text-on-inverted'),
        rule: token('--rule'),
        structure: token('--structure'),
        accent: token('--accent'),
        'accent-text': token('--accent-text'),
        focus: token('--focus'),
      },
      fontFamily: {
        display: ['var(--font-display)', 'Archivo', 'system-ui', 'sans-serif'],
        sans: ['var(--font-sans)', 'Instrument Sans', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        // Anotación: siempre monoespaciada, siempre pequeña, siempre en caja alta.
        note: ['0.6875rem', { lineHeight: '1.2', letterSpacing: '0.12em' }],
        'note-lg': ['0.8125rem', { lineHeight: '1.3', letterSpacing: '0.08em' }],
        'display-sm': ['clamp(1.75rem, 1.2rem + 2.4vw, 2.75rem)', { lineHeight: '0.98', letterSpacing: '-0.02em' }],
        'display-md': ['clamp(2.5rem, 1.4rem + 4.6vw, 4.5rem)', { lineHeight: '0.94', letterSpacing: '-0.03em' }],
        'display-lg': ['clamp(3.25rem, 1.2rem + 8vw, 7.5rem)', { lineHeight: '0.9', letterSpacing: '-0.035em' }],
      },
      letterSpacing: {
        cajetin: '0.18em',
      },
      spacing: {
        margin: 'var(--grid-margin)',
        gutter: 'var(--grid-gutter)',
      },
      transitionTimingFunction: {
        cota: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
      maxWidth: {
        prose: '68ch',
        lamina: '1600px',
      },
    },
  },
  plugins: [],
};

export default config;
