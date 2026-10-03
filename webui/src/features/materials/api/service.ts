/**
 * Data-access layer for the Django material API.
 *
 * This is the only file that talks to `/material/` and `/drive/` — components
 * consume these functions, never `apiClient` directly (mirrors the auth
 * feature's `api/service.ts`).
 */

import { apiClient } from '@/lib/api-client';
import type {
  CreateLinkMaterialPayload,
  DriveBrowseResponse,
  Material,
  Paginated
} from './types';

/** Lists materials (DRF paginated envelope), one page at a time. */
export async function listMaterials(page = 1): Promise<Paginated<Material>> {
  const query = page > 1 ? `?page=${page}` : '';
  return apiClient<Paginated<Material>>(`/material/${query}`);
}

/** Creates a link material (JSON body — no multipart branch in `apiClient`). */
export async function createLinkMaterial(
  payload: CreateLinkMaterialPayload
): Promise<Material> {
  return apiClient<Material>('/material/', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

/** Deletes a material by id (lecturer/admin only; backend is the authority). */
export async function deleteMaterial(id: number): Promise<void> {
  return apiClient<void>(`/material/${id}/`, { method: 'DELETE' });
}

/**
 * Lists one Shared Drive folder's children for the browse picker.
 * Omit `parent` for the configured root. Throws `ApiRequestError` (503 when
 * the Drive integration is unconfigured) — callers branch on `error.status`.
 */
export async function browseDrive(parent?: string): Promise<DriveBrowseResponse> {
  const query = parent ? `?parent=${encodeURIComponent(parent)}` : '';
  return apiClient<DriveBrowseResponse>(`/drive/${query}`);
}
