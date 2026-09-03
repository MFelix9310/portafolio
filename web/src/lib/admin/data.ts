import 'server-only';

import { adminApi } from './api';
import type { ResourceKey } from './resources';
import type { AdminRow, AdminSubarea } from './types';

/**
 * Lecturas del panel. Todas van contra `/api/v1/admin/*`, que incluye borradores.
 *
 * Nota de contrato: el backend no expone `GET /admin/{recurso}/{id}` (A11 define
 * `GetProjectById` en la capa de aplicación, pero no hay ruta HTTP). Para editar se
 * pide el listado y se busca el id en memoria.
 *
 * Revisado con el catálogo reconstruido (2026-08-31): 23 proyectos, 67 filas de
 * media, y el resto de colecciones por debajo de la decena. `GET /admin/projects`
 * devuelve 78 kB en 29 ms contra el backend local; además la página de edición es
 * `force-dynamic`, así que no hay caché que invalidar ni ISR que retrasar.
 * **Se deja como está.**
 *
 * El umbral para pedir la ruta `GET /admin/{recurso}/{id}` es que el listado
 * pase de unos cientos de filas o de ~1 MB: a partir de ahí se descarga un
 * catálogo entero para editar un campo y deja de compensar.
 */
export async function listRows(resource: ResourceKey): Promise<AdminRow[]> {
  return adminApi.get<AdminRow[]>(`/admin/${resource}`);
}

export async function findRow(resource: ResourceKey, id: string): Promise<AdminRow | null> {
  const rows = await listRows(resource);
  return rows.find((row) => row.id === id) ?? null;
}

export interface SubareaOption {
  area: string;
  key: string;
  label: string;
}

export async function subareaOptions(): Promise<SubareaOption[]> {
  const rows = await adminApi.get<AdminSubarea[]>('/admin/subareas');
  return rows.map((row) => ({
    area: row.area,
    key: row.key,
    label: row.name?.es ?? row.key,
  }));
}
