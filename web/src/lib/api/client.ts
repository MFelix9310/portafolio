/**
 * Cliente HTTP del backend FastAPI (`/api/v1`, ver docs/02-contrato-datos.md).
 *
 * Si `NEXT_PUBLIC_API_URL` no está definida, `apiEnabled()` es falso y la capa de
 * datos cae al seed. Si está definida pero el backend no responde, se registra el
 * fallo y también se cae al seed: una página en blanco no es una opción.
 */

export const REVALIDATE_SECONDS = Number(process.env.NEXT_PUBLIC_REVALIDATE ?? 300);

function baseUrl(): string | null {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!raw) return null;
  return raw.replace(/\/+$/, '');
}

export function apiEnabled(): boolean {
  return baseUrl() !== null;
}

export async function apiGet<T>(path: string, search?: Record<string, string | undefined>): Promise<T | null> {
  const base = baseUrl();
  if (!base) return null;

  const url = new URL(`${base}/api/v1${path}`);
  for (const [key, value] of Object.entries(search ?? {})) {
    if (value) url.searchParams.set(key, value);
  }

  try {
    const response = await fetch(url, {
      headers: { accept: 'application/json' },
      next: { revalidate: REVALIDATE_SECONDS, tags: ['catalog'] },
    });
    if (!response.ok) {
      console.warn(`[api] ${url.pathname} respondió ${response.status}; se usa el seed`);
      return null;
    }
    return (await response.json()) as T;
  } catch (error) {
    console.warn(`[api] ${url.pathname} inalcanzable; se usa el seed`, error);
    return null;
  }
}
