'use client';

import { Icons } from '@/components/icons';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { browseDrive } from '@/features/materials/api/service';
import type { DriveBrowseEntry } from '@/features/materials/api/types';
import { useMessages } from '@/i18n/use-messages';
import { ApiRequestError } from '@/lib/api-client';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

interface Crumb {
  id: string;
  name: string;
}

/**
 * Shared Drive browse-and-pick dialog (rev.3).
 *
 * Read-only: descends folders via `GET /api/v1/drive/` and, on file selection,
 * hands the API-provided canonical `url` back to the caller (the form fills
 * `source_url`). Honest states only — a 503 (integration unconfigured) never
 * degrades into a fake list, and an empty folder says so.
 */
export function BrowseDriveDialog({
  open,
  onOpenChange,
  onSelect
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (url: string) => void;
}) {
  const t = useMessages();
  const [stack, setStack] = useState<Crumb[]>([]);

  const current = stack.at(-1);
  const parent = current?.id;

  const { data, isLoading, error } = useQuery({
    queryKey: ['drive-browse', parent ?? 'root'],
    queryFn: () => browseDrive(parent),
    enabled: open
  });

  const notConfigured =
    (error instanceof ApiRequestError && error.status === 503) ||
    data?.configured === false;

  const serverError = error instanceof ApiRequestError && error.status === 502;

  const results = data?.results ?? [];

  function descend(entry: DriveBrowseEntry) {
    setStack((prev) => [...prev, { id: entry.id, name: entry.name }]);
  }

  function goBack() {
    setStack((prev) => prev.slice(0, -1));
  }

  function handleSelect(entry: DriveBrowseEntry) {
    onSelect(entry.url);
    onOpenChange(false);
  }

  // Reset to the root each time the dialog is closed so it never reopens deep.
  function handleOpenChange(next: boolean) {
    if (!next) setStack([]);
    onOpenChange(next);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className='sm:max-w-lg'>
        <DialogHeader>
          <DialogTitle>{t.materials.browse.title}</DialogTitle>
          <DialogDescription>{t.materials.browse.description}</DialogDescription>
        </DialogHeader>

        <div className='flex items-center gap-2'>
          <Button
            type='button'
            variant='outline'
            size='icon-sm'
            onClick={goBack}
            disabled={stack.length === 0}
            aria-label={t.materials.browse.back}
          >
            <Icons.chevronLeft />
          </Button>
          <nav aria-label={t.materials.browse.title} className='text-muted-foreground truncate text-sm'>
            <span className='text-foreground font-medium'>{t.materials.browse.root}</span>
            {stack.map((crumb) => (
              <span key={crumb.id}>
                {' / '}
                <span>{crumb.name}</span>
              </span>
            ))}
          </nav>
        </div>

        <div className='min-h-40 max-h-72 overflow-y-auto rounded-lg ring-1 ring-foreground/10'>
          {isLoading ? (
            <div className='flex flex-col gap-2 p-3' role='status' aria-label={t.materials.browse.loading}>
              {[0, 1, 2].map((index) => (
                <Skeleton key={index} className='h-8 w-full' />
              ))}
            </div>
          ) : notConfigured ? (
            <p className='text-muted-foreground p-4 text-sm'>{t.materials.browse.unavailable}</p>
          ) : serverError ? (
            <p className='text-destructive p-4 text-sm'>{t.materials.browse.errorServer}</p>
          ) : error ? (
            <p className='text-destructive p-4 text-sm'>{t.materials.browse.error}</p>
          ) : results.length === 0 ? (
            <p className='text-muted-foreground p-4 text-sm'>{t.materials.browse.empty}</p>
          ) : (
            <ul className='flex flex-col'>
              {results.map((entry) => (
                <li key={entry.id}>
                  <div className='flex items-center gap-2 border-b px-3 py-2 last:border-b-0'>
                    <span className='text-muted-foreground shrink-0'>
                      {entry.isFolder ? <Icons.workspace /> : <Icons.page />}
                    </span>
                    {entry.isFolder ? (
                      <button
                        type='button'
                        onClick={() => descend(entry)}
                        className='flex-1 truncate text-left text-sm hover:underline'
                      >
                        {entry.name}
                      </button>
                    ) : (
                      <>
                        <span className='flex-1 truncate text-sm'>{entry.name}</span>
                        <Button
                          type='button'
                          variant='outline'
                          size='xs'
                          onClick={() => handleSelect(entry)}
                        >
                          {t.materials.browse.select}
                        </Button>
                      </>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {data?.truncated && (
          <p className='text-muted-foreground text-xs'>{t.materials.browse.truncated}</p>
        )}

        <DialogFooter>
          <DialogClose render={<Button type='button' variant='outline' />}>
            {t.materials.cancel}
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
