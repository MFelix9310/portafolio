import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

import {
  ADMIN_SESSION_COOKIE,
  SUPABASE_ANON_KEY,
  SUPABASE_URL,
  devTokenModeEnabled,
  supabaseConfigured,
} from '@/lib/admin/config';

/** Rutas del panel que tienen que ser alcanzables sin sesión. */
const PUBLIC_ADMIN_PATHS = ['/admin/login', '/admin/auth/callback'];

function isPublicAdminPath(pathname: string): boolean {
  return PUBLIC_ADMIN_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

function toLogin(request: NextRequest): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = '/admin/login';
  url.search = '';
  // Volver donde estaba después de entrar; es la diferencia entre una herramienta
  // y un laberinto.
  if (request.nextUrl.pathname !== '/admin') {
    url.searchParams.set('next', request.nextUrl.pathname);
  }
  return NextResponse.redirect(url);
}

/**
 * Conveniencia de UX, **no** control de acceso. La autorización real vive en
 * `require_admin` de FastAPI y en las políticas RLS de Postgres; este middleware
 * solo evita que Félix vea una pantalla vacía cuando la sesión caduca.
 */
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const response = NextResponse.next({ request });

  if (supabaseConfigured()) {
    const supabase = createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll: (list) => {
          for (const { name, value, options } of list) response.cookies.set(name, value, options);
        },
      },
    });
    // getUser() y no getSession(): valida el token contra Supabase en vez de
    // fiarse de una cookie que cualquiera puede escribir.
    const { data } = await supabase.auth.getUser();
    if (!data.user && !isPublicAdminPath(pathname)) return toLogin(request);
    if (data.user && pathname === '/admin/login') {
      return NextResponse.redirect(new URL('/admin', request.url));
    }
    return response;
  }

  if (devTokenModeEnabled()) {
    const cookie = request.cookies.get(ADMIN_SESSION_COOKIE)?.value;
    const signedIn = Boolean(cookie) && cookie === process.env.ADMIN_DEV_TOKEN;
    if (!signedIn && !isPublicAdminPath(pathname)) return toLogin(request);
    if (signedIn && pathname === '/admin/login') {
      return NextResponse.redirect(new URL('/admin', request.url));
    }
    return response;
  }

  // Sin ningún modo de acceso configurado sólo se puede llegar al login, que
  // explica qué falta por configurar.
  if (!isPublicAdminPath(pathname)) return toLogin(request);
  return response;
}

export const config = {
  matcher: ['/admin/:path*'],
};
