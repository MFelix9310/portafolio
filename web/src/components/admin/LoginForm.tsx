'use client';

import { useActionState, useState } from 'react';

import { devLoginAction, type LoginState } from '@/lib/admin/auth-actions';
import { browserSupabase } from '@/lib/admin/supabase-browser';
import { Button, Notice } from './ui';

const INPUT =
  'w-full border border-content/25 bg-surface px-2 py-2 text-[14px] text-content placeholder:text-faint';

/**
 * Contraseña como metodo principal: el usuario admin se crea desde la API de
 * administracion con contraseña, y depender del correo para cada acceso al
 * panel era una friccion sin beneficio. No hay pantalla de registro: la fila
 * de `admin_users` se inserta a mano en la base.
 */
function Password({ next }: { next: string }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const { error: authError } = await browserSupabase().auth.signInWithPassword({
      email: email.trim(),
      password,
    });
    if (authError) {
      setBusy(false);
      setError(authError.message);
      return;
    }
    // El cliente de navegador ya dejo la sesion en cookies; una navegacion
    // completa hace que el middleware y el servidor la vean.
    window.location.assign(next);
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="space-y-1">
        <label htmlFor="email" className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
          Correo
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className={INPUT}
          placeholder="tu@correo.com"
        />
      </div>
      <div className="space-y-1">
        <label htmlFor="password" className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
          Contraseña
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className={INPUT}
        />
      </div>
      <Button type="submit" variant="primary" disabled={busy || !email.trim() || !password}>
        {busy ? 'Entrando…' : 'Entrar'}
      </Button>
      {error && <Notice tone="error">{error}</Notice>}
    </form>
  );
}

/** Enlace magico como alternativa, por si se olvida la contraseña. */
function MagicLink({ next }: { next: string }) {
  const [email, setEmail] = useState('');
  const [state, setState] = useState<{ tone: 'error' | 'success'; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setState(null);
    const redirect = new URL('/admin/auth/callback', window.location.origin);
    redirect.searchParams.set('next', next);
    const { error } = await browserSupabase().auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: redirect.toString(), shouldCreateUser: false },
    });
    setBusy(false);
    setState(
      error
        ? { tone: 'error', text: error.message }
        : { tone: 'success', text: 'Enlace enviado. Revisa el correo; caduca en una hora.' },
    );
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="space-y-1">
        <label htmlFor="email" className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
          Correo
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className={INPUT}
          placeholder="tu@correo.com"
        />
      </div>
      <Button type="submit" variant="primary" disabled={busy || !email.trim()}>
        {busy ? 'Enviando…' : 'Enviar enlace'}
      </Button>
      {state && <Notice tone={state.tone}>{state.text}</Notice>}
    </form>
  );
}

function DevToken() {
  const [state, action, pending] = useActionState<LoginState, FormData>(devLoginAction, {});
  return (
    <form action={action} className="space-y-3">
      <Notice tone="info">
        Supabase no está configurado. El panel usa el token de desarrollo, el mismo{' '}
        <code className="font-mono">DEV_ADMIN_TOKEN</code> que espera el backend.
      </Notice>
      <div className="space-y-1">
        <label htmlFor="token" className="block font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
          Token de desarrollo
        </label>
        <input id="token" name="token" type="password" required autoComplete="off" className={INPUT} />
      </div>
      <Button type="submit" variant="primary" disabled={pending}>
        {pending ? 'Entrando…' : 'Entrar'}
      </Button>
      {state.error && <Notice tone="error">{state.error}</Notice>}
    </form>
  );
}

export default function LoginForm({
  mode,
  next,
}: {
  mode: 'supabase' | 'dev' | 'unconfigured';
  next: string;
}) {
  if (mode === 'supabase') {
    return (
      <div className="space-y-6">
        <Password next={next} />
        <details className="border-t border-content/15 pt-4">
          <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
            Entrar con enlace por correo
          </summary>
          <div className="pt-3">
            <MagicLink next={next} />
          </div>
        </details>
      </div>
    );
  }
  if (mode === 'dev') return <DevToken />;
  return (
    <Notice tone="error">
      No hay ningún método de acceso configurado. Define{' '}
      <code className="font-mono">NEXT_PUBLIC_SUPABASE_URL</code> y{' '}
      <code className="font-mono">NEXT_PUBLIC_SUPABASE_ANON_KEY</code>, o{' '}
      <code className="font-mono">ADMIN_DEV_TOKEN</code> en desarrollo.
    </Notice>
  );
}
