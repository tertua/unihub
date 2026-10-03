'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Icons } from '@/components/icons';
import { useMessages } from '@/i18n/use-messages';

/**
 * Honest placeholder for product pages whose backend app is not built yet.
 * Shows no data — a missing backend is a state to communicate, not to obscure.
 */
export function NotImplemented({
  title,
  appName,
  description
}: {
  title: string;
  appName: string;
  description?: string;
}) {
  const t = useMessages();

  return (
    <Card className='mx-auto mt-8 max-w-lg'>
      <CardHeader>
        <div className='bg-muted mb-2 flex size-10 items-center justify-center rounded-lg'>
          <Icons.help className='text-muted-foreground size-5' />
        </div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>
          {t.notImplemented.prefix} <code className='font-mono'>{appName}</code>{' '}
          {t.notImplemented.suffix}
        </CardDescription>
      </CardHeader>
      {description && (
        <CardContent>
          <p className='text-muted-foreground text-sm'>{description}</p>
        </CardContent>
      )}
    </Card>
  );
}
