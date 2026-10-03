'use client';

import { Button } from '@/components/ui/button';
import { ButtonGroup } from '@/components/ui/button-group';
import { locales } from '@/i18n/config';
import { useLocale } from '@/i18n/use-messages';

/**
 * EN/ID switch. Writes the `fh_locale` cookie and refreshes the route so
 * server-rendered copy and metadata follow along — no reload needed.
 */
export function LanguageToggle() {
  const { locale, messages, setLocale } = useLocale();

  return (
    <ButtonGroup aria-label={messages.language.label}>
      {locales.map((option) => (
        <Button
          key={option}
          type='button'
          size='sm'
          variant={option === locale ? 'secondary' : 'ghost'}
          aria-pressed={option === locale}
          aria-label={messages.language[option]}
          className='px-2 text-xs'
          onClick={() => setLocale(option)}
        >
          {option.toUpperCase()}
        </Button>
      ))}
    </ButtonGroup>
  );
}
