/** `source_type` discriminator returned by the material API. */
export type MaterialSourceType = 'file' | 'link';

/** Response shape of `GET /api/v1/material/`. */
export interface Material {
  id: number;
  title: string;
  description: string;
  course: string;
  file: string | null;
  source_url: string | null;
  drive_file_id: string;
  source_type: MaterialSourceType;
  embed_url: string | null;
  drive_name: string | null;
  drive_mime_type: string | null;
  owner: number;
  created_at: string;
  updated_at: string;
}

/** DRF paginated list envelope (PAGE_SIZE = 20). */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** `POST /api/v1/material/` body — link mode only on the frontend. */
export interface CreateLinkMaterialPayload {
  title: string;
  description?: string;
  course?: string;
  source_url: string;
}

/** One entry in the Shared Drive browse response (`GET /api/v1/drive/`). */
export interface DriveBrowseEntry {
  id: string;
  name: string;
  mimeType: string;
  isFolder: boolean;
  url: string;
}

/** Response shape of the Shared Drive browse endpoint. */
export interface DriveBrowseResponse {
  configured: boolean;
  parent: string | null;
  results: DriveBrowseEntry[];
  truncated: boolean;
}
