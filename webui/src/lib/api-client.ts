/**
 * Low-level fetch wrapper for the Django `/api/v1/` backend.
 *
 * Tokens live in non-httpOnly cookies (`fh_access` / `fh_refresh`) so the
 * browser can attach them as a Bearer header. A single 401 -> refresh ->
 * retry path keeps every feature service free of auth plumbing.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api/v1';

export const ACCESS_COOKIE = 'fh_access';
export const REFRESH_COOKIE = 'fh_refresh';

// Access tokens are short-lived; refresh tokens are long-lived.
export const ACCESS_MAX_AGE = 60 * 15;
export const REFRESH_MAX_AGE = 60 * 60 * 24 * 7;

export interface ApiError {
  status: number;
  body: unknown;
}

/** Shape thrown for every non-2xx response so callers can branch on `status`. */
export class ApiRequestError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, message?: string) {
    super(message ?? `Request failed with status ${status}`);
    this.name = 'ApiRequestError';
    this.status = status;
    this.body = body;
  }
}

/** Reads a cookie by name in the browser. Returns null on the server. */
export function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

/** Writes a cookie readable by JS (never httpOnly — the client sends the Bearer header). */
export function writeCookie(name: string, value: string, maxAge: number): void {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

export function clearAuthCookies(): void {
  if (typeof document === 'undefined') return;
  const expire = '; path=/; max-age=0; SameSite=Lax';
  document.cookie = `${ACCESS_COOKIE}=${expire}`;
  document.cookie = `${REFRESH_COOKIE}=${expire}`;
}

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/** Exchanges the refresh cookie for a new access token. Returns the token or null. */
async function refreshAccessToken(): Promise<string | null> {
  const refresh = readCookie(REFRESH_COOKIE);
  if (!refresh) return null;

  const res = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh })
  });

  if (!res.ok) return null;

  const data = (await parseBody(res)) as { access?: string } | null;
  if (!data?.access) return null;

  writeCookie(ACCESS_COOKIE, data.access, ACCESS_MAX_AGE);
  return data.access;
}

async function doFetch(
  endpoint: string,
  options: RequestInit,
  accessToken: string | null
): Promise<Response> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);

  return fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
}

/**
 * Performs a JSON request against the backend.
 *
 * `auth: false` skips the Authorization header (used by login/register).
 * On a 401 the request is retried exactly once after refreshing the token.
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const { auth = true, ...init } = options;
  const accessToken = auth ? readCookie(ACCESS_COOKIE) : null;

  let res = await doFetch(endpoint, init, accessToken);

  // Single retry after refresh; if refresh fails, drop tokens and bounce to sign-in.
  if (res.status === 401 && auth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await doFetch(endpoint, init, newToken);
    } else {
      clearAuthCookies();
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/auth')) {
        window.location.href = '/auth/sign-in';
      }
      throw new ApiRequestError(401, await parseBody(res));
    }
  }

  const body = await parseBody(res);

  if (!res.ok) {
    throw new ApiRequestError(res.status, body);
  }

  return body as T;
}
