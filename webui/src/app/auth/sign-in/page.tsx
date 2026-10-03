import { SignInForm } from '@/features/auth/components/sign-in-form';
import { getMessages } from '@/i18n/get-locale';
import { Metadata } from 'next';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getMessages();
  return {
    title: t.auth.signIn.metaTitle,
    description: t.auth.signIn.metaDescription
  };
}

export default async function Page() {
  const t = await getMessages();
  return (
    <div className='bg-muted/30 flex min-h-screen flex-col items-center justify-center gap-6 p-4'>
      <div className='flex flex-col items-center gap-1 text-center'>
        <h1 className='text-2xl font-bold tracking-tight'>Faculty Learning Hub</h1>
        <p className='text-muted-foreground text-sm'>{t.auth.tagline}</p>
      </div>
      <SignInForm />
    </div>
  );
}
