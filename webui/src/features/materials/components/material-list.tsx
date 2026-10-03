'use client';

import { Icons } from '@/components/icons';
import { AlertModal } from '@/components/modal/alert-modal';
import { Button } from '@/components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { deleteMaterial, listMaterials } from '@/features/materials/api/service';
import type { Material } from '@/features/materials/api/types';
import { MaterialCard } from '@/features/materials/components/material-card';
import { useMessages } from '@/i18n/use-messages';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toast } from 'sonner';

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

/**
 * Real material list. Loading shows skeletons, an empty list is an honest empty
 * state (never mock rows), and errors surface a localized message — the feature
 * is implemented; an empty result is genuinely empty.
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
  const [pendingDelete, setPendingDelete] = useState<Material | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['materials'],
    queryFn: listMaterials
  });

  const removeMutation = useMutation({
    mutationFn: (id: number) => deleteMaterial(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['materials'] });
      setPendingDelete(null);
    },
    onError: () => {
      setPendingDelete(null);
      toast.error(t.errors.generic);
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
        </CardHeader>
      </Card>
    );
  }

  const materials = data?.results ?? [];

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
