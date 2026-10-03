'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingButton } from '@/components/ui/loading-button';
import { useAuth } from '@/features/auth/context/auth-provider';
import { parseApiError, type FieldErrors } from '@/features/auth/utils/parse-api-error';
import type { Messages } from '@/i18n/en';
import { useMessages } from '@/i18n/use-messages';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { z } from 'zod';

// Built per submit so validation copy follows the active locale.
const signInSchema = (m: Messages['auth']['signIn']) =>
  z.object({
    username: z.string().min(1, m.usernameRequired),
    password: z.string().min(1, m.passwordRequired)
  });

export function SignInForm() {
  const { login } = useAuth();
  const router = useRouter();
  const t = useMessages();

  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setFieldErrors({});

    const formData = new FormData(event.currentTarget);
    const parsed = signInSchema(t.auth.signIn).safeParse({
      username: formData.get('username'),
      password: formData.get('password')
    });

    if (!parsed.success) {
      const errors: FieldErrors = {};
      for (const issue of parsed.error.issues) {
        const key = String(issue.path[0]);
        errors[key] = [...(errors[key] ?? []), issue.message];
      }
      setFieldErrors(errors);
      return;
    }

    setPending(true);
    try {
      await login(parsed.data);
      router.push('/dashboard/overview');
    } catch (error) {
      const { fieldErrors: fe, formError: form } = parseApiError(error, t.errors);
      setFieldErrors(fe);
      setFormError(form);
    } finally {
      setPending(false);
    }
  }

  return (
    <Card className='w-full max-w-md'>
      <CardHeader>
        <CardTitle>{t.auth.signIn.title}</CardTitle>
        <CardDescription>{t.auth.signIn.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className='flex flex-col gap-4' noValidate>
          <div className='flex flex-col gap-2'>
            <Label htmlFor='username'>Username</Label>
            <Input id='username' name='username' autoComplete='username' required />
            {fieldErrors.username && (
              <p className='text-destructive text-xs'>{fieldErrors.username.join(' ')}</p>
            )}
          </div>

          <div className='flex flex-col gap-2'>
            <Label htmlFor='password'>Password</Label>
            <Input
              id='password'
              name='password'
              type='password'
              autoComplete='current-password'
              required
            />
            {fieldErrors.password && (
              <p className='text-destructive text-xs'>{fieldErrors.password.join(' ')}</p>
            )}
          </div>

          {formError && <p className='text-destructive text-sm'>{formError}</p>}

          <LoadingButton type='submit' loading={pending} className='w-full'>
            {t.auth.signIn.submit}
          </LoadingButton>

          <p className='text-muted-foreground text-center text-sm'>
            {t.auth.signIn.noAccount}{' '}
            <Link href='/auth/sign-up' className='text-primary underline-offset-4 hover:underline'>
              {t.auth.signIn.createAccount}
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
