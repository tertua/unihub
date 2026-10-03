'use client';

import PageContainer from '@/components/layout/page-container';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingButton } from '@/components/ui/loading-button';
import { useAuth } from '@/features/auth/context/auth-provider';
import * as authService from '@/features/auth/api/service';
import { parseApiError } from '@/features/auth/utils/parse-api-error';
import { useMessages } from '@/i18n/use-messages';
import { toast } from 'sonner';
import { useState } from 'react';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const t = useMessages();

  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setFieldErrors({});

    const formData = new FormData(event.currentTarget);
    setPending(true);
    try {
      await authService.updateMe({
        first_name: String(formData.get('first_name') ?? ''),
        last_name: String(formData.get('last_name') ?? ''),
        email: String(formData.get('email') ?? ''),
        study_program: String(formData.get('study_program') ?? '')
      });
      await refreshUser();
      toast.success(t.profile.saved);
    } catch (error) {
      const { fieldErrors: fe, formError: form } = parseApiError(error, t.errors);
      setFieldErrors(fe);
      setFormError(form);
    } finally {
      setPending(false);
    }
  }

  if (!user) {
    return (
      <PageContainer pageTitle={t.profile.title}>
        <p className='text-muted-foreground text-sm'>{t.profile.loading}</p>
      </PageContainer>
    );
  }

  const identityIdNumber =
    user.role === 'student' ? user.student_id_number : user.lecturer_id_number;
  const roleLabels = t.profile.roles as Record<string, string>;

  return (
    <PageContainer pageTitle={t.profile.title} pageDescription={t.profile.description}>
      <Card className='max-w-2xl'>
        <CardHeader>
          <CardTitle>{t.profile.accountInfo}</CardTitle>
          <CardDescription>{t.profile.identityNote}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className='flex flex-col gap-4'>
            <div className='grid grid-cols-1 gap-4 sm:grid-cols-2'>
              <div className='flex flex-col gap-2'>
                <Label htmlFor='username'>{t.profile.username}</Label>
                <Input id='username' value={user.username} disabled />
              </div>
              <div className='flex flex-col gap-2'>
                <Label htmlFor='role'>{t.profile.role}</Label>
                <Input id='role' value={roleLabels[user.role] ?? user.role} disabled />
              </div>
              {identityIdNumber && (
                <div className='flex flex-col gap-2'>
                  <Label htmlFor='id_number'>
                    {user.role === 'student' ? 'NIM' : 'NIP'}
                  </Label>
                  <Input id='id_number' value={identityIdNumber} disabled />
                </div>
              )}
            </div>

            <div className='grid grid-cols-1 gap-4 sm:grid-cols-2'>
              <div className='flex flex-col gap-2'>
                <Label htmlFor='first_name'>{t.profile.firstName}</Label>
                <Input id='first_name' name='first_name' defaultValue={user.first_name} />
                {fieldErrors.first_name && (
                  <p className='text-destructive text-xs'>{fieldErrors.first_name.join(' ')}</p>
                )}
              </div>
              <div className='flex flex-col gap-2'>
                <Label htmlFor='last_name'>{t.profile.lastName}</Label>
                <Input id='last_name' name='last_name' defaultValue={user.last_name} />
                {fieldErrors.last_name && (
                  <p className='text-destructive text-xs'>{fieldErrors.last_name.join(' ')}</p>
                )}
              </div>
            </div>

            <div className='flex flex-col gap-2'>
              <Label htmlFor='email'>{t.profile.email}</Label>
              <Input id='email' name='email' type='email' defaultValue={user.email} />
              {fieldErrors.email && (
                <p className='text-destructive text-xs'>{fieldErrors.email.join(' ')}</p>
              )}
            </div>

            <div className='flex flex-col gap-2'>
              <Label htmlFor='study_program'>{t.profile.studyProgram}</Label>
              <Input
                id='study_program'
                name='study_program'
                defaultValue={user.study_program ?? ''}
              />
              {fieldErrors.study_program && (
                <p className='text-destructive text-xs'>{fieldErrors.study_program.join(' ')}</p>
              )}
            </div>

            {formError && <p className='text-destructive text-sm'>{formError}</p>}

            <div className='flex justify-end'>
              <LoadingButton type='submit' loading={pending}>
                {t.profile.save}
              </LoadingButton>
            </div>
          </form>
        </CardContent>
      </Card>
    </PageContainer>
  );
}
