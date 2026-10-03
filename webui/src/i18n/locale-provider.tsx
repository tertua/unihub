'use client';

/**
 * Holds the active locale for client components.
 *
 * The server reads the same `fh_locale` cookie (see `get-locale.ts`), so the
 * value passed in as `initialLocale` matches what was rendered on the server —
 * no hydration flash. Switching writes the cookie and refreshes the router so
 * server components (metadata, page copy) re-render in the new locale.
 */

import { useRouter } from 'next/navigation';
import { createContext, useCallback, useMemo, useState } from 'react';
import { LOCALE_COOKIE, type Locale } from './config';
import type { Messages } from './en';
import { getCatalog } from './index';

interface LocaleContextValue {
  locale: Locale;
  messages: Messages;
  setLocale: (next: Locale) => void;
}

export const LocaleContext = createContext<LocaleContextValue | undefined>(undefined);

export function LocaleProvider({
  initialLocale,
  children
}: {
  initialLocale: Locale;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [locale, setLocaleState] = useState<Locale>(initialLocale);

  const setLocale = useCallback(
    (next: Locale) => {
      setLocaleState(next);
      // Read by the server on the next request; must stay non-httpOnly.
      document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
      router.refresh();
    },
    [router]
  );

  const value = useMemo<LocaleContextValue>(
    () => ({ locale, messages: getCatalog(locale), setLocale }),
    [locale, setLocale]
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}
