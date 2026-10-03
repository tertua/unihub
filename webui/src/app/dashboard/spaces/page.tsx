import PageContainer from '@/components/layout/page-container';
import { NotImplemented } from '@/components/not-implemented';
import { getMessages } from '@/i18n/get-locale';
import { Metadata } from 'next';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getMessages();
  return {
    title: 'Space',
    description: t.pages.spaces.description
  };
}

export default async function SpacesPage() {
  const t = await getMessages();
  return (
    <PageContainer pageTitle='Space' pageDescription={t.pages.spaces.description}>
      <NotImplemented title='Space' appName='spaces' />
    </PageContainer>
  );
}
