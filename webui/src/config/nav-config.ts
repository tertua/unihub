import type { Messages } from '@/i18n/en';
import { NavGroup } from '@/types';

/**
 * Navigation for the Faculty Learning Hub app shell.
 *
 * Built from the active catalog so sidebar and Cmd+K labels follow the
 * selected locale. Groups render as labelled sidebar sections and feed the
 * Cmd+K palette.
 * `access.roles` is a client-side visibility hint only — the backend is the
 * source of truth for every API call.
 */
export function getNavGroups(nav: Messages['nav']): NavGroup[] {
  return [
    {
      label: nav.overview,
      items: [
        {
          title: nav.dashboard,
          url: '/dashboard/overview',
          icon: 'dashboard',
          isActive: false,
          shortcut: ['d', 'd'],
          items: []
        }
      ]
    },
    {
      label: nav.learning,
      items: [
        {
          title: 'Material Hub',
          url: '/dashboard/materials',
          icon: 'page',
          isActive: false,
          items: []
        },
        {
          title: 'Space',
          url: '/dashboard/spaces',
          icon: 'workspace',
          isActive: false,
          items: []
        },
        {
          title: 'AI Chat',
          url: '/dashboard/chat',
          icon: 'chat',
          isActive: false,
          items: []
        }
      ]
    },
    {
      label: nav.lecturers,
      items: [
        {
          title: 'Tool Kit',
          url: '/dashboard/tools',
          icon: 'adjustments',
          isActive: false,
          items: [],
          access: { roles: ['lecturer', 'admin'] }
        }
      ]
    },
    {
      label: nav.account,
      items: [
        {
          title: nav.profile,
          url: '/dashboard/profile',
          icon: 'profile',
          isActive: false,
          items: []
        }
      ]
    }
  ];
}
