'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingButton } from '@/components/ui/loading-button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { useAuth } from '@/features/auth/context/auth-provider';
import { parseApiError, type FieldErrors } from '@/features/auth/utils/parse-api-error';
import type { Messages } from '@/i18n/en';
import { useMessages } from '@/i18n/use-messages';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { z } from 'zod';

// Built per submit so validation copy follows the active locale.
const signUpSchema = (m: Messages['auth']['signUp']) =>
  z
    .object({
      username: z.string().min(1, m.usernameRequired),
      password: z
        .string()
        .min(8, m.passwordMin)
        .refine((value) => !/^\d+$/.test(value), m.passwordNumeric),
      role: z.enum(['student', 'lecturer']),
      student_id_number: z.string().optional(),
      study_program: z.string().optional()
    })
    .refine((data) => data.role !== 'student' || (data.student_id_number ?? '').trim().length > 0, {
      message: m.nimRequired,
      path: ['student_id_number']
    });

export function SignUpForm() {
  const { register } = useAuth();
  const router = useRouter();
  const t = useMessages();

  const [role, setRole] = useState<'student' | 'lecturer'>('student');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setFieldErrors({});

    const formData = new FormData(event.currentTarget);
    const studentId = String(formData.get('student_id_number') ?? '').trim();
    const studyProgram = String(formData.get('study_program') ?? '').trim();

    const parsed = signUpSchema(t.auth.signUp).safeParse({
      username: formData.get('username'),
      password: formData.get('password'),
      role,
      student_id_number: studentId || undefined,
      study_program: studyProgram || undefined
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
      await register(parsed.data);
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
        <CardTitle>{t.auth.signUp.title}</CardTitle>
        <CardDescription>{t.auth.signUp.description}</CardDescription>
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
              autoComplete='new-password'
              required
            />
            {fieldErrors.password && (
              <p className='text-destructive text-xs'>{fieldErrors.password.join(' ')}</p>
            )}
          </div>

          <div className='flex flex-col gap-2'>
            <Label htmlFor='role'>{t.auth.signUp.role}</Label>
            <Select
              value={role}
              onValueChange={(value) => setRole(value as 'student' | 'lecturer')}
            >
              <SelectTrigger id='role' className='w-full'>
                <SelectValue placeholder={t.auth.signUp.rolePlaceholder} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='student'>{t.auth.signUp.student}</SelectItem>
                <SelectItem value='lecturer'>{t.auth.signUp.lecturer}</SelectItem>
              </SelectContent>
            </Select>
            {fieldErrors.role && (
              <p className='text-destructive text-xs'>{fieldErrors.role.join(' ')}</p>
            )}
          </div>

          {role === 'student' && (
            <div className='flex flex-col gap-2'>
              <Label htmlFor='student_id_number'>NIM</Label>
              <Input id='student_id_number' name='student_id_number' />
              {fieldErrors.student_id_number && (
                <p className='text-destructive text-xs'>
                  {fieldErrors.student_id_number.join(' ')}
                </p>
              )}
            </div>
          )}

          <div className='flex flex-col gap-2'>
            <Label htmlFor='study_program'>{t.auth.signUp.studyProgram}</Label>
            <Input id='study_program' name='study_program' />
            {fieldErrors.study_program && (
              <p className='text-destructive text-xs'>{fieldErrors.study_program.join(' ')}</p>
            )}
          </div>

          {formError && <p className='text-destructive text-sm'>{formError}</p>}

          <LoadingButton type='submit' loading={pending} className='w-full'>
            {t.auth.signUp.submit}
          </LoadingButton>

          <p className='text-muted-foreground text-center text-sm'>
            {t.auth.signUp.haveAccount}{' '}
            <Link href='/auth/sign-in' className='text-primary underline-offset-4 hover:underline'>
              {t.auth.signUp.signIn}
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
