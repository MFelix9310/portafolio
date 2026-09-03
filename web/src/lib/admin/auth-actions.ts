'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { ADMIN_SESSION_COOKIE, devTokenModeEnabled } from './config';
import { signOutSession } from './session';

export interface LoginState {
  error?: string;
  notice?: string;
}

/**
 * Entrada en modo desarrollo. Espejo de `AUTH_BACKEND=dev` del backend: el token
 * que se teclea aquí es el mismo que FastAPI espera, así que si no coincide, el
 * panel entra pero la API le cierra la puerta en la primera llamada.
 */
export async function devLoginAction(_: LoginState, formData: FormData): Promise<LoginState> {
  if (!devTokenModeEnabled()) {
    return { error: 'El modo desarrollo no está disponible en esta instalación.' };
  }
  const token = String(formData.get('token') ?? '').trim();
  if (!token) return { error: 'Escribe el token de desarrollo.' };
  if (token !== process.env.ADMIN_DEV_TOKEN) return { error: 'Token incorrecto.' };

  const store = await cookies();
  store.set(ADMIN_SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60 * 8,
  });
  redirect('/admin');
}

export async function signOutAction(): Promise<void> {
  await signOutSession();
  redirect('/admin/login');
}
