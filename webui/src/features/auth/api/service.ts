/**
 * Data-access layer for the Django auth API.
 *
 * This is the only file that talks to `/auth/*` — components and the
 * AuthProvider consume these functions, never `apiClient` directly.
 */

import {
  ACCESS_COOKIE,
  ACCESS_MAX_AGE,
  API_BASE_URL,
  ApiRequestError,
  REFRESH_COOKIE,
  REFRESH_MAX_AGE,
  apiClient,
  clearAuthCookies,
  writeCookie
} from '@/lib/api-client';
import type { LoginPayload, RegisterPayload, TokenPair, UpdateMePayload, User } from './types';

/** Registers a new account. The backend rejects `role: 'admin'` with 400. */
export async function register(payload: RegisterPayload): Promise<User> {
  return apiClient<User>('/auth/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
    auth: false
  });
}

/**
 * Authenticates and persists both tokens as JS-readable cookies.
 * Returns the freshly fetched profile so callers have a ready user object.
 */
export async function login(payload: LoginPayload): Promise<User> {
  const tokens = await apiClient<TokenPair>('/auth/token/', {
    method: 'POST',
    body: JSON.stringify(payload),
    auth: false
  });

  writeCookie(ACCESS_COOKIE, tokens.access, ACCESS_MAX_AGE);
  writeCookie(REFRESH_COOKIE, tokens.refresh, REFRESH_MAX_AGE);

  return me();
}

/** Fetches the current profile. Throws `ApiRequestError` 401 when the token is invalid. */
export async function me(): Promise<User> {
  return apiClient<User>('/auth/me/');
}

/** Updates editable profile fields. Identity fields are ignored by the backend. */
export async function updateMe(payload: UpdateMePayload): Promise<User> {
  return apiClient<User>('/auth/me/', {
    method: 'PATCH',
    body: JSON.stringify(payload)
  });
}

/**
 * Clears local auth state. There is no server-side logout endpoint, so this
 * only drops the cookie pair.
 */
export function logout(): void {
  clearAuthCookies();
}

/** True when a stored access token exists (presence only — validity is the server's call). */
export function hasStoredSession(): boolean {
  if (typeof document === 'undefined') return false;
  return document.cookie.includes(`${ACCESS_COOKIE}=`);
}

export { API_BASE_URL, ApiRequestError };
