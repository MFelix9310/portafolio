import Link from 'next/link';
import { redirect } from 'next/navigation';

import AdminNav from '@/components/admin/AdminNav';
import RevalidateButton from '@/components/admin/RevalidateButton';
import { Button } from '@/components/admin/ui';
import { signOutAction } from '@/lib/admin/auth-actions';
import { getAdminSession } from '@/lib/admin/session';

/** Todo lo que cuelga de aquí exige sesión. El login queda fuera de este grupo. */
export default async function PanelLayout({ children }: { children: React.ReactNode }) {
  const session = await getAdminSession();
  if (!session) redirect('/admin/login');

  return (
    <div className="min-h-screen">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-content/25 px-3 py-2">
        <div className="flex items-baseline gap-3">
          <Link href="/admin" className="font-mono text-[12px] uppercase tracking-[0.18em]">
            Panel
          </Link>
          <Link
            href="/"
            className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted hover:text-content"
          >
            Ver el sitio ↗
          </Link>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <RevalidateButton />
          <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">
            {session.email}
            {session.mode === 'dev' && ' · modo dev'}
          </span>
          <form action={signOutAction}>
            <Button type="submit" variant="quiet">
              Salir
            </Button>
          </form>
        </div>
      </header>

      <div className="md:flex">
        <AdminNav />
        <main id="contenido" className="min-w-0 flex-1 p-3 md:p-4">
          {children}
        </main>
      </div>
    </div>
  );
}
