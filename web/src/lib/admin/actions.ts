'use server';

import { revalidatePath } from 'next/cache';

import { adminApi, attempt } from './api';
import { toPayload, validate, type FormValues } from './form-model';
import { RESOURCES, isResourceKey, type ResourceKey } from './resources';
import type { AdminMedia, Status, UploadTicket } from './types';

export interface ActionResult<T = unknown> {
  ok: boolean;
  message?: string;
  code?: string;
  fieldErrors?: Record<string, string>;
  data?: T;
}

function refreshPanel(resource?: string): void {
  revalidatePath('/admin', 'layout');
  if (resource) revalidatePath(`/admin/${resource}`);
}

/** Publicar sin revalidar deja el sitio igual y el panel parece roto. */
async function revalidateFrontend(): Promise<void> {
  await attempt(() => adminApi.post('/admin/revalidate', {}));
}

export async function saveResourceAction(
  resource: string,
  id: string | null,
  values: FormValues,
): Promise<ActionResult<{ id: string | null }>> {
  if (!isResourceKey(resource)) return { ok: false, message: 'Recurso desconocido.' };
  const def = RESOURCES[resource as ResourceKey];

  // Validación de servidor: el cliente ya validó, pero esa no cuenta.
  const fieldErrors = validate(def, values);
  if (Object.keys(fieldErrors).length > 0) {
    return { ok: false, message: 'Revisa los campos marcados.', fieldErrors };
  }

  if (!id && !def.canCreate) {
    return { ok: false, message: `No se pueden crear ${def.label.toLowerCase()}.` };
  }

  const payload = toPayload(def, values);
  const result = await attempt(async () => {
    if (!id) return adminApi.post<{ id: string | null }>(`/admin/${resource}`, payload);
    if (def.updateMethod === 'POST') {
      return adminApi.post<{ id: string | null }>(`/admin/${resource}`, { ...payload, id });
    }
    return adminApi.patch<{ id: string | null }>(`/admin/${resource}/${id}`, payload);
  });

  if (!result.ok) return { ok: false, message: result.message, code: result.code };

  refreshPanel(resource);
  if (payload.status === 'published') await revalidateFrontend();
  return { ok: true, data: result.data };
}

export async function deleteResourceAction(
  resource: string,
  id: string,
): Promise<ActionResult> {
  if (!isResourceKey(resource)) return { ok: false, message: 'Recurso desconocido.' };
  if (!RESOURCES[resource as ResourceKey].canDelete) {
    return { ok: false, message: 'Este recurso no admite borrado.' };
  }
  const result = await attempt(() => adminApi.del(`/admin/${resource}/${id}`));
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  refreshPanel(resource);
  await revalidateFrontend();
  return { ok: true };
}

export async function setStatusAction(
  resource: string,
  id: string,
  status: Status,
): Promise<ActionResult> {
  if (!isResourceKey(resource)) return { ok: false, message: 'Recurso desconocido.' };
  const result = await attempt(() => adminApi.patch(`/admin/${resource}/${id}`, { status }));
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  refreshPanel(resource);
  await revalidateFrontend();
  return { ok: true };
}

export async function reorderAction(resource: string, ids: string[]): Promise<ActionResult> {
  if (!isResourceKey(resource)) return { ok: false, message: 'Recurso desconocido.' };
  if (!RESOURCES[resource as ResourceKey].canReorder) {
    return { ok: false, message: 'Este recurso no admite reordenar.' };
  }
  if (ids.length === 0) return { ok: false, message: 'Nada que reordenar.' };
  const result = await attempt(() => adminApi.post(`/admin/${resource}/reorder`, { ids }));
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  refreshPanel(resource);
  await revalidateFrontend();
  return { ok: true };
}

export async function saveProfileAction(values: FormValues): Promise<ActionResult> {
  const headline = values.headline as { es: string; en: string };
  const bio = values.bio as { es: string; en: string };
  const fieldErrors: Record<string, string> = {};
  if (!String(values.name ?? '').trim()) fieldErrors.name = 'Obligatorio.';
  if (!headline?.es.trim()) fieldErrors.headline = 'El castellano es obligatorio.';
  if (!bio?.es.trim()) fieldErrors.bio = 'El castellano es obligatorio.';
  if (Object.keys(fieldErrors).length > 0) {
    return { ok: false, message: 'Revisa los campos marcados.', fieldErrors };
  }

  const localized = (value: { es: string; en: string }) =>
    value.en.trim() ? { es: value.es.trim(), en: value.en.trim() } : { es: value.es.trim() };

  const payload = {
    name: String(values.name).trim(),
    headline: localized(headline),
    bio: localized(bio),
    photo_path: String(values.photo_path ?? '').trim() || null,
    professional_photo_path: String(values.professional_photo_path ?? '').trim() || null,
    status: String(values.status ?? 'published'),
  };

  const result = await attempt(() => adminApi.post('/admin/profile', payload));
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  refreshPanel('profile');
  await revalidateFrontend();
  return { ok: true };
}

export async function revalidateAction(): Promise<ActionResult<{ detail: string }>> {
  const result = await attempt(() =>
    adminApi.post<{ accepted: boolean; detail: string }>('/admin/revalidate', {}),
  );
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  return {
    ok: true,
    message: result.data.accepted
      ? 'Revalidación aceptada por el frontend.'
      : `Revalidación no aplicada: ${result.data.detail}`,
  };
}

// --- media -------------------------------------------------------------------

export async function createUploadUrlAction(
  filename: string,
  contentType: string,
): Promise<ActionResult<UploadTicket>> {
  const result = await attempt(() =>
    adminApi.post<UploadTicket>('/admin/media/upload-url', {
      filename,
      content_type: contentType,
    }),
  );
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  return { ok: true, data: result.data };
}

export async function saveMediaAction(
  payload: Record<string, unknown>,
): Promise<ActionResult<AdminMedia>> {
  const result = await attempt(() => adminApi.post<AdminMedia>('/admin/media', payload));
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  refreshPanel('projects');
  return { ok: true, data: result.data };
}

export async function deleteMediaAction(id: string): Promise<ActionResult> {
  const result = await attempt(() => adminApi.del(`/admin/media/${id}`));
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  refreshPanel('projects');
  return { ok: true };
}

export async function reorderMediaAction(ids: string[]): Promise<ActionResult> {
  const result = await attempt(() => adminApi.post('/admin/media/reorder', { ids }));
  if (!result.ok) return { ok: false, message: result.message, code: result.code };
  refreshPanel('projects');
  return { ok: true };
}
