import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { FlatCompat } from '@eslint/eslintrc';

/**
 * Config plana de ESLint 9.
 *
 * Antes `pnpm lint` ejecutaba `next lint` sin configuración ni dependencia: el
 * comando abría un asistente interactivo y salía con error en cualquier CI. Se
 * pasa al CLI de ESLint, que es lo que `next lint` recomienda ahora que está
 * deprecado y desaparece en Next 16.
 *
 * `next/core-web-vitals` es lo que hace que valgan de algo los
 * `eslint-disable-next-line @next/next/no-img-element` que ya estaban escritos
 * por el código: sin config no había regla que desactivar.
 */
const compat = new FlatCompat({ baseDirectory: dirname(fileURLToPath(import.meta.url)) });

const config = [
  {
    ignores: ['.next/**', 'node_modules/**', 'next-env.d.ts', 'public/**'],
  },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    rules: {
      // El guion bajo delante ya es la forma de decir "esto no se usa a propósito".
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrors: 'none',
        },
      ],
    },
  },
  {
    // `scripts/` son utilidades de Node, no código de la app.
    files: ['scripts/**/*.mjs'],
    rules: {
      'no-console': 'off',
    },
  },
];

export default config;
