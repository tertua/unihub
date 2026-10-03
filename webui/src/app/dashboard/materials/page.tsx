import { MaterialsPageClient } from '@/features/materials/components/materials-page-client';
import { getMessages } from '@/i18n/get-locale';
import { Metadata } from 'next';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getMessages();
  return {
    title: t.materials.title,
    description: t.materials.description
  };
}

export default async function MaterialsPage() {
  const t = await getMessages();
  return (
    <MaterialsPageClient
      pageTitle={t.materials.title}
      pageDescription={t.materials.description}
    />
  );
}
