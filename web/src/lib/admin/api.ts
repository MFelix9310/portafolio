import 'server-only';

import { adminApiBaseUrl } from './config';
import { getAdminSession } from './session';

/** Error de la API con el código que devolvió el backend, ya legible. */
export class AdminApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly code = 'error',
  ) {
    super(message);
    this.name = 'AdminApiError';
  }

  /** 409 = el cuerpo es correcto pero choca con el estado (slug repetido, etc.). */
  get isConflict(): boolean {
    return this.status === 409;
  }

  get isUnauthorized(): boolean {
    return this.status === 401 || this.status === 403;
  }
}

type ErrorBody = {
  error?: { code?: string; message?: string };
  detail?: string | { loc?: (string | number)[]; msg?: string }[];
};

/** El backend habla tres dialectos de error; aquí se reducen a uno. */
function readError(status: number, body: unknown): AdminApiError {
  const payload = (body ?? {}) as ErrorBody;
  if (payload.error?.message) {
    return new AdminApiError(status, payload.error.message, payload.error.code ?? 'error');
  }
  if (typeof payload.detail === 'string') {
    return new AdminApiError(status, payload.detail);
  }
  if (Array.isArray(payload.detail)) {
    const lines = payload.detail.map((item) => {
      const field = (item.loc ?? []).filter((part) => part !== 'body').join('.');
      return field ? `${field}: ${item.msg ?? 'inválido'}` : (item.msg ?? 'inválido');
    });
    return new AdminApiError(status, lines.join('; ') || 'entrada inválida', 'invalid_input');
  }
  return new AdminApiError(status, `la API respondió ${status}`);
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  search?: Record<string, string | undefined>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const base = adminApiBaseUrl();
  if (!base) {
    throw new AdminApiError(
      503,
      'ADMIN_API_URL no está configurada: el panel no sabe a qué backend hablar.',
      'not_configured',
    );
  }

  const session = await getAdminSession();
  if (!session) throw new AdminApiError(401, 'sesión de administración caducada', 'unauthorized');

  const url = new URL(`${base}/api/v1${path}`);
  for (const [key, value] of Object.entries(options.search ?? {})) {
    if (value !== undefined && value !== '') url.searchParams.set(key, value);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: options.method ?? 'GET',
      cache: 'no-store',
      headers: {
        accept: 'application/json',
        authorization: `Bearer ${session.token}`,
        ...(options.body === undefined ? {} : { 'content-type': 'application/json' }),
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (cause) {
    throw new AdminApiError(
      503,
      `el backend no responde en ${base}. ¿Está levantado?`,
      'unreachable',
    );
  }

  if (response.status === 204) return undefined as T;

  const raw = await response.text();
  const parsed: unknown = raw ? JSON.parse(raw) : null;
  if (!response.ok) throw readError(response.status, parsed);
  return parsed as T;
}

export const adminApi = {
  get: <T>(path: string, search?: Record<string, string | undefined>) =>
    request<T>(path, { search }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body }),
  del: (path: string) => request<void>(path, { method: 'DELETE' }),
};

/** Envuelve una llamada para que el error viaje como dato y no como excepción. */
export async function attempt<T>(
  run: () => Promise<T>,
): Promise<{ ok: true; data: T } | { ok: false; message: string; code: string }> {
  try {
    return { ok: true, data: await run() };
  } catch (error) {
    if (error instanceof AdminApiError) {
      return { ok: false, message: error.message, code: error.code };
    }
    return { ok: false, message: (error as Error).message, code: 'unexpected' };
  }
}
