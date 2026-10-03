'use client';

import { Icons } from '@/components/icons';
import { AlertModal } from '@/components/modal/alert-modal';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { deleteMaterial, listMaterials } from '@/features/materials/api/service';
import type { Material } from '@/features/materials/api/types';
import { MaterialCard } from '@/features/materials/components/material-card';
import type { Messages } from '@/i18n/en';
import { useMessages } from '@/i18n/use-messages';
import { ApiRequestError } from '@/lib/api-client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toast } from 'sonner';

/** Matches the backend's `PAGE_SIZE` (DRF `PageNumberPagination`). */
const PAGE_SIZE = 20;

function MaterialListSkeleton() {
  return (
    <div className='flex flex-col gap-4' role='status' aria-label='Loading materials'>
      {[0, 1, 2].map((index) => (
        <Card key={index}>
          <CardHeader>
            <Skeleton className='h-5 w-1/2' />
            <Skeleton className='h-4 w-1/3' />
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}

/** Status-aware copy for a failed delete (403/404/5xx get their own message). */
function deleteErrorMessage(error: unknown, errors: Messages['errors']): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 403) return errors.forbidden;
    if (error.status === 404) return errors.notFound;
    if (error.status >= 500) return errors.server;
  }
  return errors.generic;
}

/**
 * Real material list. Loading shows skeletons, an empty list is an honest empty
 * state (never mock rows), and errors surface a localized message with a retry
 * action — the feature is implemented; an empty result is genuinely empty.
 */
export function MaterialList({
  canManage,
  onAdd
}: {
  canManage: boolean;
  onAdd?: () => void;
}) {
  const t = useMessages();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pendingDelete, setPendingDelete] = useState<Material | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['materials', page],
    queryFn: () => listMaterials(page)
  });

  const removeMutation = useMutation({
    mutationFn: (id: number) => deleteMaterial(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['materials'] });
      setPendingDelete(null);
    },
    onError: (error) => {
      setPendingDelete(null);
      toast.error(deleteErrorMessage(error, t.errors));
    }
  });

  if (isLoading) {
    return <MaterialListSkeleton />;
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t.materials.title}</CardTitle>
          <CardDescription>{t.errors.generic}</CardDescription>
          <Button variant='outline' size='sm' onClick={() => void refetch()}>
            {t.errors.retry}
          </Button>
        </CardHeader>
      </Card>
    );
  }

  const materials = data?.results ?? [];
  const count = data?.count ?? 0;
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));

  if (materials.length === 0) {
    return (
      <Card className='mx-auto mt-4 max-w-lg'>
        <CardHeader>
          <div className='bg-muted mb-2 flex size-10 items-center justify-center rounded-lg'>
            <Icons.page className='text-muted-foreground size-5' />
          </div>
          <CardTitle>{t.materials.emptyTitle}</CardTitle>
          <CardDescription>{t.materials.emptyDescription}</CardDescription>
        </CardHeader>
        {canManage && onAdd && (
          <div className='px-(--card-spacing) pb-(--card-spacing)'>
            <Button onClick={onAdd}>
              <Icons.add data-icon='inline-start' />
              {t.materials.add}
            </Button>
          </div>
        )}
      </Card>
    );
  }

  return (
    <>
      <div className='flex flex-col gap-4'>
        {materials.map((material) => (
          <MaterialCard
            key={material.id}
            material={material}
            canManage={canManage}
            onDelete={setPendingDelete}
          />
        ))}
      </div>

      <div className='flex items-center justify-between gap-4 pt-2'>
        <Button
          variant='outline'
          size='sm'
          disabled={data?.previous === null || page <= 1}
          onClick={() => setPage((current) => Math.max(1, current - 1))}
        >
          <Icons.chevronLeft data-icon='inline-start' />
          {t.materials.pagination.previous}
        </Button>
        <span className='text-muted-foreground text-sm'>
          {t.materials.pagination.pageOf(page, totalPages)}
        </span>
        <Button
          variant='outline'
          size='sm'
          disabled={data?.next === null || page >= totalPages}
          onClick={() => setPage((current) => current + 1)}
        >
          {t.materials.pagination.next}
          <Icons.chevronRight data-icon='inline-end' />
        </Button>
      </div>

      <AlertModal
        isOpen={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) removeMutation.mutate(pendingDelete.id);
        }}
        loading={removeMutation.isPending}
        title={t.materials.deleteTitle}
        description={t.materials.deleteDescription}
        confirmLabel={t.materials.delete}
      />
    </>
  );
}
