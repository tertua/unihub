'use client';

/**
 * Client-side navigation filtering for UI visibility only.
 *
 * The backend is the security boundary; this hook just hides items the
 * signed-in role cannot use, so the sidebar and Cmd+K palette stay honest.
 */

import { useAuth } from '@/features/auth/context/auth-provider';
import type { NavItem, NavGroup, PermissionCheck } from '@/types';
import { useMemo } from 'react';

const hasAccess = (access: PermissionCheck | undefined, role: string | undefined): boolean => {
  if (!access) return true;

  // This app has no organization concept; such items never show.
  if (access.requireOrg) return false;

  // No server-side permission/plan/feature source exists yet — hide to be safe.
  if (access.permission || access.plan || access.feature) return false;

  if (access.roles && (!role || !access.roles.includes(role as never))) return false;

  return true;
};

export function useFilteredNavItems(items: NavItem[]) {
  const { user } = useAuth();
  const role = user?.role;

  return useMemo(
    () =>
      items
        .filter((item) => hasAccess(item.access, role))
        .map((item) => {
          if (!item.items || item.items.length === 0) return item;
          return { ...item, items: item.items.filter((child) => hasAccess(child.access, role)) };
        }),
    [items, role]
  );
}

export function useFilteredNavGroups(groups: NavGroup[]) {
  const allItems = useMemo(() => groups.flatMap((g) => g.items), [groups]);
  const filteredItems = useFilteredNavItems(allItems);

  return useMemo(() => {
    const visibleTitles = new Set(filteredItems.map((item) => item.title));
    return groups
      .map((group) => ({
        ...group,
        items: group.items.filter((item) => visibleTitles.has(item.title))
      }))
      .filter((group) => group.items.length > 0);
  }, [groups, filteredItems]);
}
