import PageContainer from '@/components/layout/page-container';
import { NotImplemented } from '@/components/not-implemented';
import { getMessages } from '@/i18n/get-locale';
import { Metadata } from 'next';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getMessages();
  return {
    title: 'Tool Kit',
    description: t.pages.tools.description
  };
}

export default async function ToolsPage() {
  const t = await getMessages();
  return (
    <PageContainer pageTitle='Tool Kit' pageDescription={t.pages.tools.description}>
      <NotImplemented
        title='Tool Kit'
        appName='tools'
        description={t.pages.tools.note}
      />
    </PageContainer>
  );
}
