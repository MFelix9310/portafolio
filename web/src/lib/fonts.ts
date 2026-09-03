import { Archivo, Instrument_Sans, JetBrains_Mono } from 'next/font/google';

/**
 * Display en Archivo con su eje de anchura real (`wdth`): en caps y con tracking
 * negativo da el peso de un cajetín sin caer en las grotescas quemadas.
 * `latin-ext` no es opcional — el contenido está en español y lleva acentos.
 */
export const display = Archivo({
  subsets: ['latin', 'latin-ext'],
  axes: ['wdth'],
  display: 'swap',
  variable: '--font-display',
});

export const sans = Instrument_Sans({
  subsets: ['latin', 'latin-ext'],
  display: 'swap',
  variable: '--font-sans',
});

export const mono = JetBrains_Mono({
  subsets: ['latin', 'latin-ext'],
  display: 'swap',
  variable: '--font-mono',
});

export const fontVariables = `${display.variable} ${sans.variable} ${mono.variable}`;
