import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

import { SUPABASE_ANON_KEY, SUPABASE_URL, supabaseConfigured } from '@/lib/admin/config';

/**
 * Aterrizaje del magic link: cambia el código por una sesión y planta las cookies.
 *
 * Que la sesión exista no significa que el usuario sea admin. Eso lo deciden
 * `require_admin` de FastAPI y RLS; aquí solo se establece la identidad.
 */
export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl;
  const code = searchParams.get('code');
  const rawNext = searchParams.get('next');
  const next = rawNext && rawNext.startsWith('/admin') ? rawNext : '/admin';

  if (!supabaseConfigured()) {
    return NextResponse.redirect(`${origin}/admin/login`);
  }
  if (!code) {
    return NextResponse.redirect(`${origin}/admin/login?error=sin-codigo`);
  }

  const response = NextResponse.redirect(`${origin}${next}`);
  const supabase = createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (list) => {
        for (const { name, value, options } of list) response.cookies.set(name, value, options);
      },
    },
  });

  const { error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) {
    return NextResponse.redirect(
      `${origin}/admin/login?error=${encodeURIComponent(error.message)}`,
    );
  }
  return response;
}
