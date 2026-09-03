import LoginForm from '@/components/admin/LoginForm';
import { devTokenModeEnabled, supabaseConfigured } from '@/lib/admin/config';

export const dynamic = 'force-dynamic';

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;
  // Solo se acepta una ruta interna del panel: un `next` externo sería un redirector.
  const target = next && next.startsWith('/admin') ? next : '/admin';

  const mode = supabaseConfigured() ? 'supabase' : devTokenModeEnabled() ? 'dev' : 'unconfigured';

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4">
      <h1 className="font-mono text-[12px] uppercase tracking-[0.18em] text-muted">
        Panel de administración
      </h1>
      <p className="mt-2 text-[13px] text-muted">
        Acceso solo para Félix. No hay registro: la cuenta se da de alta en la base.
      </p>
      <div className="mt-6">
        <LoginForm mode={mode} next={target} />
      </div>
    </main>
  );
}
