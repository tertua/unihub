import { defaultLocale, type Locale } from './config';
import { en, type Messages } from './en';
import { id } from './id';

const catalogs: Record<Locale, Messages> = { en, id };

/** Pure lookup — safe to import from server and client code alike. */
export function getCatalog(locale: Locale): Messages {
  return catalogs[locale] ?? catalogs[defaultLocale];
}

export type { Locale, Messages };
