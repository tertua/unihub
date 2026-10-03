'use client';

import PageContainer from '@/components/layout/page-container';
import { Icons } from '@/components/icons';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/features/auth/context/auth-provider';
import { MaterialLinkForm } from '@/features/materials/components/material-link-form';
import { MaterialList } from '@/features/materials/components/material-list';
import { useMessages } from '@/i18n/use-messages';
import { useState } from 'react';

/**
 * Client island for `/dashboard/materials`: owns the query, the add-material
 * toggle, and the create form. The route itself stays a server component
 * (metadata + i18n) and passes the localized strings down.
 */
export function MaterialsPageClient({
  pageTitle,
  pageDescription
}: {
  pageTitle: string;
  pageDescription: string;
}) {
  const t = useMessages();
  const { user } = useAuth();
  const [showForm, setShowForm] = useState(false);

  const canManage = user?.role === 'lecturer' || user?.role === 'admin';

  return (
    <PageContainer
      pageTitle={pageTitle}
      pageDescription={pageDescription}
      pageHeaderAction={
        canManage && !showForm ? (
          <Button onClick={() => setShowForm(true)}>
            <Icons.add data-icon='inline-start' />
            {t.materials.add}
          </Button>
        ) : undefined
      }
    >
      <div className='flex flex-col gap-4'>
        {showForm && (
          <MaterialLinkForm
            onCancel={() => {
              setShowForm(false);
            }}
          />
        )}
        <MaterialList canManage={canManage} onAdd={() => setShowForm(true)} />
      </div>
    </PageContainer>
  );
}
