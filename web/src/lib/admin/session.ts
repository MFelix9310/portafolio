import 'server-only';

import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

import {
  ADMIN_SESSION_COOKIE,
  SUPABASE_ANON_KEY,
  SUPABASE_URL,
  devTokenModeEnabled,
  supabaseConfigured,
} from './config';

export interface AdminSession {
  /** Bearer que viaja a `/api/v1/admin/*`. El backend lo verifica de verdad. */
  token: string;
  email: string;
  mode: 'supabase' | 'dev';
}

async function serverSupabase() {
  const store = await cookies();
  return createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => store.getAll(),
      setAll: (list) => {
        // En un Server Component las cookies son de solo lectura; la renovación la
        // hace el middleware. Aquí se ignora sin ruido, que es el patrón oficial.
        try {
          for (const { name, value, options } of list) store.set(name, value, options);
        } catch {
          /* noop */
        }
      },
    },
  });
}

/**
 * Sesión actual, o `null`. Nunca lanza: la decisión de redirigir es de quien llama.
 *
 * El middleware ya bloquea `/admin/*` sin sesión, pero eso es conveniencia de UX; la
 * autorización real la imponen `require_admin` de FastAPI y RLS de Postgres.
 */
export async function getAdminSession(): Promise<AdminSession | null> {
  if (supabaseConfigured()) {
    const supabase = await serverSupabase();
    const { data } = await supabase.auth.getUser();
    if (!data.user) return null;
    const { data: sessionData } = await supabase.auth.getSession();
    const token = sessionData.session?.access_token;
    if (!token) return null;
    return { token, email: data.user.email ?? 'admin', mode: 'supabase' };
  }

  if (devTokenModeEnabled()) {
    const store = await cookies();
    const cookie = store.get(ADMIN_SESSION_COOKIE)?.value;
    const expected = process.env.ADMIN_DEV_TOKEN ?? '';
    if (cookie && expected && cookie === expected) {
      return { token: expected, email: 'dev@localhost', mode: 'dev' };
    }
  }

  return null;
}

export async function signOutSession(): Promise<void> {
  if (supabaseConfigured()) {
    const supabase = await serverSupabase();
    await supabase.auth.signOut();
    return;
  }
  const store = await cookies();
  store.delete(ADMIN_SESSION_COOKIE);
}
