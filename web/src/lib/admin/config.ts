/**
 * Configuración del panel. Un único sitio donde se decide qué modo de acceso hay.
 *
 * El modo `dev` es el espejo exacto de `AUTH_BACKEND=dev` del backend: existe para
 * poder ejercitar `/admin` sin proyecto de Supabase. Es deliberadamente incapaz de
 * activarse en producción — hacen falta las tres condiciones a la vez.
 */

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() ?? '';
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() ?? '';

export function supabaseConfigured(): boolean {
  return SUPABASE_URL.length > 0 && SUPABASE_ANON_KEY.length > 0;
}

/** Solo servidor: nunca se importa desde un componente cliente. */
export function devTokenModeEnabled(): boolean {
  if (supabaseConfigured()) return false;
  if (process.env.NODE_ENV === 'production') return false;
  return (process.env.ADMIN_DEV_TOKEN ?? '').length > 0;
}

export function adminApiBaseUrl(): string {
  const raw = (process.env.ADMIN_API_URL || process.env.NEXT_PUBLIC_API_URL || '').trim();
  return raw.replace(/\/+$/, '');
}

export const ADMIN_SESSION_COOKIE = 'admin-dev-session';

/** Por encima de esto se avisa de pasar el vídeo por `tools/media` antes de subir. */
export const VIDEO_WARN_BYTES = 15 * 1024 * 1024;
