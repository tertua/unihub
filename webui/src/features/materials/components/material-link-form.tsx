'use client';

import { Icons } from '@/components/icons';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { useAppForm } from '@/lib/form';
import { createLinkMaterial } from '@/features/materials/api/service';
import type { CreateLinkMaterialPayload } from '@/features/materials/api/types';
import { BrowseDriveDialog } from '@/features/materials/components/browse-drive-dialog';
import { isDriveUrl } from '@/features/materials/utils/drive-url';
import { parseApiError } from '@/features/auth/utils/parse-api-error';
import type { Messages } from '@/i18n/en';
import { useMessages } from '@/i18n/use-messages';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';

/** Built per submit so validation copy follows the active locale. */
const linkMaterialSchema = (m: Messages['materials']['form']) =>
  z.object({
    title: z.string().trim().min(1, m.titleRequired),
    course: z.string().trim().optional(),
    description: z.string().trim().optional(),
    source_url: z
      .string()
      .trim()
      .min(1, m.urlRequired)
      .refine(isDriveUrl, { message: m.urlInvalid })
  });

type LinkMaterialValues = z.infer<ReturnType<typeof linkMaterialSchema>>;

const defaultValues: LinkMaterialValues = {
  title: '',
  course: '',
  description: '',
  source_url: ''
};

/**
 * Add-material form — link mode only (`type='url'`). Follows the design
 * contract (TanStack `useAppForm` + `TextField`/`TextareaField`); on success it
 * invalidates the material list and resets. 400 field errors map under the
 * matching inputs via `parseApiError`.
 */
export function MaterialLinkForm({ onCancel }: { onCancel?: () => void }) {
  const t = useMessages();
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [browseOpen, setBrowseOpen] = useState(false);

  const form = useAppForm({
    defaultValues,
    validators: {
      onSubmit: linkMaterialSchema(t.materials.form)
    },
    onSubmit: async ({ value }) => {
      setFormError(null);
      setFieldErrors({});
      const payload: CreateLinkMaterialPayload = {
        title: value.title,
        course: value.course || undefined,
        description: value.description || undefined,
        source_url: value.source_url
      };
      try {
        await createLinkMaterial(payload);
        await queryClient.invalidateQueries({ queryKey: ['materials'] });
        form.reset();
        toast.success(t.materials.form.created);
      } catch (error) {
        const { fieldErrors: fe, formError: formMessage } = parseApiError(error, t.errors);
        setFieldErrors(fe);
        setFormError(formMessage);
      }
    }
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t.materials.form.title}</CardTitle>
        <CardDescription>{t.materials.form.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            event.stopPropagation();
            void form.handleSubmit();
          }}
          className='flex flex-col gap-4'
          noValidate
        >
          <form.AppField
            name='title'
            children={(field) => (
              <field.TextField label={t.materials.form.titleLabel} required />
            )}
          />

          <form.AppField
            name='course'
            children={(field) => <field.TextField label={t.materials.form.courseLabel} />}
          />

          <form.AppField
            name='source_url'
            children={(field) => (
              <div className='flex flex-col gap-2'>
                <field.TextField
                  label={t.materials.form.urlLabel}
                  required
                  type='url'
                  inputMode='url'
                  placeholder='https://drive.google.com/...'
                />
                <div>
                  <Button
                    type='button'
                    variant='outline'
                    size='sm'
                    onClick={() => setBrowseOpen(true)}
                  >
                    <Icons.workspace data-icon='inline-start' />
                    {t.materials.form.browse}
                  </Button>
                </div>
              </div>
            )}
          />

          <form.AppField
            name='description'
            children={(field) => (
              <field.TextareaField label={t.materials.form.descriptionLabel} rows={3} />
            )}
          />

          {fieldErrors.source_url && (
            <p className='text-destructive text-xs'>{fieldErrors.source_url.join(' ')}</p>
          )}
          {fieldErrors.title && (
            <p className='text-destructive text-xs'>{fieldErrors.title.join(' ')}</p>
          )}
          {formError && <p className='text-destructive text-sm'>{formError}</p>}

          <p className='text-muted-foreground text-xs'>{t.materials.form.sourceNote}</p>

          <div className='flex items-center justify-end gap-2'>
            {onCancel && (
              <Button type='button' variant='outline' onClick={onCancel}>
                {t.materials.cancel}
              </Button>
            )}
            <form.AppForm>
              <form.SubmitButton>{t.materials.form.submit}</form.SubmitButton>
            </form.AppForm>
          </div>
        </form>

        <BrowseDriveDialog
          open={browseOpen}
          onOpenChange={setBrowseOpen}
          onSelect={(url) => form.setFieldValue('source_url', url)}
        />
      </CardContent>
    </Card>
  );
}
