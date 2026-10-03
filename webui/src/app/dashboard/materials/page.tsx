import PageContainer from '@/components/layout/page-container';
import { NotImplemented } from '@/components/not-implemented';
import { getMessages } from '@/i18n/get-locale';
import { Metadata } from 'next';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getMessages();
  return {
    title: 'Material Hub',
    description: t.pages.materials.description
  };
}

export default async function MaterialsPage() {
  const t = await getMessages();
  return (
    <PageContainer pageTitle='Material Hub' pageDescription={t.pages.materials.description}>
      <NotImplemented title='Material Hub' appName='materials' />
    </PageContainer>
  );
}
