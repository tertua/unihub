/**
 * Locale configuration for the string catalog in `src/i18n/`.
 *
 * Two locales only: the UI is English/Indonesian by product decision, and a
 * full i18n library would cost more than it returns for this size of app.
 */

export const locales = ['en', 'id'] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'en';

/**
 * Cookie carrying the active locale. Deliberately not httpOnly so both the
 * server (`next/headers`) and client components can read the same value.
 */
export const LOCALE_COOKIE = 'fh_locale';

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (locales as readonly string[]).includes(value);
}

/** Missing or unsupported cookie values fall back to the default locale. */
export function resolveLocale(raw: string | undefined | null): Locale {
  return isLocale(raw) ? raw : defaultLocale;
}
