'use client';

import { getNavGroups } from '@/config/nav-config';
import type { Messages } from '@/i18n/en';
import { useMessages } from '@/i18n/use-messages';
import { usePathname } from 'next/navigation';
import { useMemo } from 'react';

type BreadcrumbItem = {
  title: string;
  link: string;
};

// Catalog titles for the two routes the nav config cannot label well here:
// the dashboard root is not listed at all, and the overview page is labelled
// "Dashboard" there, which would repeat the root crumb.
const routeTitles: Record<string, (t: Messages) => string> = {
  '/dashboard': (t) => t.nav.dashboard,
  '/dashboard/overview': (t) => t.nav.overview
};

// Last resort for unknown deep links, so a crumb never renders empty.
function humanize(segment: string): string {
  return segment.charAt(0).toUpperCase() + segment.slice(1);
}

export function useBreadcrumbs(): BreadcrumbItem[] {
  const pathname = usePathname();
  const t = useMessages();

  return useMemo(() => {
    // Reuse the sidebar's route → label mapping (locale-aware for nav keys;
    // product names such as Material Hub or Tool Kit are identical everywhere).
    const titles = new Map<string, string>();
    for (const group of getNavGroups(t.nav)) {
      for (const item of group.items) {
        titles.set(item.url, item.title);
      }
    }

    const segments = pathname.split('/').filter(Boolean);
    return segments.map((segment, index) => {
      const link = `/${segments.slice(0, index + 1).join('/')}`;
      return {
        title: routeTitles[link]?.(t) ?? titles.get(link) ?? humanize(segment),
        link
      };
    });
  }, [pathname, t]);
}
