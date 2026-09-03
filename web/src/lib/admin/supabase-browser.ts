'use client';

import { createBrowserClient } from '@supabase/ssr';
import type { SupabaseClient } from '@supabase/supabase-js';

import { SUPABASE_ANON_KEY, SUPABASE_URL, supabaseConfigured } from './config';

let cached: SupabaseClient | null = null;

/** Cliente de navegador. Solo se usa para autenticar: nunca para leer o escribir contenido. */
export function browserSupabase(): SupabaseClient {
  if (!supabaseConfigured()) {
    throw new Error('Supabase no está configurado: falta NEXT_PUBLIC_SUPABASE_URL/ANON_KEY');
  }
  cached ??= createBrowserClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  return cached;
}
