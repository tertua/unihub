const DRIVE_HOSTS = ['drive.google.com', 'docs.google.com'];

/**
 * True when `raw` parses as a URL on an allow-listed Drive host.
 *
 * This is a narrow client-side mirror of the backend host allowlist, used only
 * by the form's Zod schema to prevent obviously-bad submits. It is **not** a
 * security boundary — the backend re-validates and owns the Drive ID
 * extraction, so the path regexes live there only (less drift).
 */
export function isDriveUrl(raw: string): boolean {
  try {
    const url = new URL(raw.trim());
    return DRIVE_HOSTS.includes(url.hostname.toLowerCase());
  } catch {
    return false;
  }
}
