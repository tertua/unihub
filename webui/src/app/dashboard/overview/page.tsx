'use client';

import PageContainer from '@/components/layout/page-container';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Icons } from '@/components/icons';
import { useAuth } from '@/features/auth/context/auth-provider';
import type { UserRole } from '@/features/auth/api/types';
import type { Messages } from '@/i18n/en';
import { useMessages } from '@/i18n/use-messages';
import Link from 'next/link';

type DescriptionKey = keyof Messages['overview']['components'];

interface ComponentLink {
  title: string;
  descriptionKey: DescriptionKey;
  url: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: UserRole[];
}

// Product names stay as-is in every locale; descriptions come from the catalog.
const COMPONENTS: ComponentLink[] = [
  {
    title: 'Material Hub',
    descriptionKey: 'materials',
    url: '/dashboard/materials',
    icon: Icons.page
  },
  {
    title: 'Space',
    descriptionKey: 'spaces',
    url: '/dashboard/spaces',
    icon: Icons.workspace
  },
  {
    title: 'AI Chat',
    descriptionKey: 'chat',
    url: '/dashboard/chat',
    icon: Icons.chat
  },
  {
    title: 'Tool Kit',
    descriptionKey: 'tools',
    url: '/dashboard/tools',
    icon: Icons.adjustments,
    roles: ['lecturer', 'admin']
  }
] as const;

export default function OverviewPage() {
  const { user } = useAuth();
  const t = useMessages();
  const displayName = user ? `${user.first_name} ${user.last_name}`.trim() || user.username : '';

  const visibleComponents = COMPONENTS.filter(
    (component) => !component.roles || (user && component.roles.includes(user.role))
  );

  return (
    <PageContainer
      pageTitle={displayName ? t.overview.greeting(displayName) : t.overview.welcome}
      pageDescription={t.overview.description}
    >
      <div className='grid grid-cols-1 gap-4 md:grid-cols-2'>
        {visibleComponents.map((component) => {
          const Icon = component.icon;
          return (
            <Link
              key={component.url}
              href={component.url}
              aria-label={component.title}
              className='group'
            >
              <Card className='h-full transition-colors group-hover:border-primary/50'>
                <CardHeader>
                  <div className='bg-muted mb-2 flex size-10 items-center justify-center rounded-lg'>
                    <Icon className='size-5' />
                  </div>
                  <CardTitle>{component.title}</CardTitle>
                  <CardDescription>{t.overview.components[component.descriptionKey]}</CardDescription>
                </CardHeader>
                <CardContent>
                  <span className='text-primary inline-flex items-center text-sm font-medium'>
                    {t.overview.open} <Icons.arrowRight className='ml-1 size-4' />
                  </span>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </PageContainer>
  );
}
