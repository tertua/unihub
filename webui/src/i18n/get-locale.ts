import { cookies } from 'next/headers';
import { LOCALE_COOKIE, resolveLocale, type Locale } from './config';
import { getCatalog, type Messages } from './index';

/** Active locale for the current request — server components only. */
export async function getLocale(): Promise<Locale> {
  const cookieStore = await cookies();
  return resolveLocale(cookieStore.get(LOCALE_COOKIE)?.value);
}

/** Active string catalog for the current request — server components only. */
export async function getMessages(): Promise<Messages> {
  return getCatalog(await getLocale());
}
