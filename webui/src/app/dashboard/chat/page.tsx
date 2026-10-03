import PageContainer from '@/components/layout/page-container';
import { NotImplemented } from '@/components/not-implemented';
import { getMessages } from '@/i18n/get-locale';
import { Metadata } from 'next';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getMessages();
  return {
    title: 'AI Chat',
    description: t.pages.chat.description
  };
}

export default async function ChatPage() {
  const t = await getMessages();
  return (
    <PageContainer pageTitle='AI Chat' pageDescription={t.pages.chat.description}>
      <NotImplemented title='AI Chat' appName='chat' />
    </PageContainer>
  );
}
