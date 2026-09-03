import ProfileForm from '@/components/admin/ProfileForm';
import { Notice, Panel } from '@/components/admin/ui';
import { adminApi, attempt } from '@/lib/admin/api';
import type { AdminProfile } from '@/lib/admin/types';

export const dynamic = 'force-dynamic';

export default async function ProfilePage() {
  const result = await attempt(() => adminApi.get<AdminProfile | null>('/admin/profile'));

  return (
    <div className="space-y-3">
      <h1 className="font-mono text-[12px] uppercase tracking-[0.18em] text-muted">Perfil</h1>
      {!result.ok ? (
        <Notice tone="error">No se pudo cargar el perfil: {result.message}</Notice>
      ) : (
        <Panel>
          <div className="p-3">
            <ProfileForm row={(result.data as Record<string, unknown> | null) ?? null} />
          </div>
        </Panel>
      )}
    </div>
  );
}
