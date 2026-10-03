import Providers from '@/components/layout/providers';
import { Toaster } from '@/components/ui/sonner';
import { fontVariables } from '@/components/themes/font.config';
import { DEFAULT_THEME, THEMES } from '@/components/themes/theme.config';
import ThemeProvider from '@/components/themes/theme-provider';
import { getLocale, getMessages } from '@/i18n/get-locale';
import { LocaleProvider } from '@/i18n/locale-provider';
import { cn } from '@/lib/utils';
import type { Metadata, Viewport } from 'next';
import { cookies } from 'next/headers';
import NextTopLoader from 'nextjs-toploader';
import { NuqsAdapter } from 'nuqs/adapters/next/app';
import '../styles/globals.css';

const META_THEME_COLORS = {
  light: '#ffffff',
  dark: '#09090b'
};

// Localized at request time so the meta description follows the active locale.
export async function generateMetadata(): Promise<Metadata> {
  const t = await getMessages();
  const appUrl = process.env.NEXT_PUBLIC_APP_URL;

  return {
    ...(appUrl ? { metadataBase: new URL(appUrl) } : {}),
    title: {
      default: 'Faculty Learning Hub',
      template: '%s | Faculty Learning Hub'
    },
    description: t.app.description,
    openGraph: {
      title: 'Faculty Learning Hub',
      description: t.app.description,
      siteName: 'Faculty Learning Hub',
      type: 'website'
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Faculty Learning Hub',
      description: t.app.description
    }
  };
}

export const viewport: Viewport = {
  themeColor: META_THEME_COLORS.light
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await getLocale();
  const cookieStore = await cookies();
  const activeThemeValue = cookieStore.get('active_theme')?.value;
  const isValidTheme = THEMES.some((t) => t.value === activeThemeValue);
  const themeToApply = isValidTheme ? activeThemeValue! : DEFAULT_THEME;

  return (
    <html lang={locale} suppressHydrationWarning data-theme={themeToApply}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                // Set meta theme color
                if (localStorage.theme === 'dark' || ((!('theme' in localStorage) || localStorage.theme === 'system') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', '${META_THEME_COLORS.dark}')
                }
              } catch (_) {}
            `
          }}
        />
      </head>
      <body
        className={cn(
          'bg-background overflow-x-hidden overscroll-none font-sans antialiased',
          fontVariables
        )}
      >
        <NextTopLoader color='var(--primary)' showSpinner={false} />
        <NuqsAdapter>
          <ThemeProvider
            attribute='class'
            defaultTheme='system'
            enableSystem
            disableTransitionOnChange
            enableColorScheme
          >
            <LocaleProvider initialLocale={locale}>
              <Providers activeThemeValue={themeToApply}>
                <Toaster />
                {children}
              </Providers>
            </LocaleProvider>
          </ThemeProvider>
        </NuqsAdapter>
      </body>
    </html>
  );
}
