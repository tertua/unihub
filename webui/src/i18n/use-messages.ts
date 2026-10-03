'use client';

import { useContext } from 'react';
import type { Locale } from './config';
import type { Messages } from './en';
import { LocaleContext } from './locale-provider';

interface LocaleState {
  locale: Locale;
  messages: Messages;
  setLocale: (next: Locale) => void;
}

/** Locale + catalog + switcher for client components. */
export function useLocale(): LocaleState {
  const value = useContext(LocaleContext);
  if (!value) {
    throw new Error('useLocale must be used inside <LocaleProvider> in the root layout.');
  }
  return value;
}

/** Just the active string catalog — the common case. */
export function useMessages(): Messages {
  return useLocale().messages;
}
