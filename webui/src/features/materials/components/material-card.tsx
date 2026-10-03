'use client';

import { Icons } from '@/components/icons';
import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import type { Material } from '@/features/materials/api/types';
import { useMessages } from '@/i18n/use-messages';

/**
 * Renders one material from the real API.
 *
 * Link materials with a file `embed_url` show an iframe preview (P4); folder
 * links degrade to a plain "Open in Drive" row. File materials link to the
 * stored `file` URL (unchanged — it points at Drive when Drive storage is
 * active). No upload UI, no mock data.
 */
export function MaterialCard({
  material,
  canManage,
  onDelete
}: {
  material: Material;
  canManage: boolean;
  onDelete: (material: Material) => void;
}) {
  const t = useMessages();
  const isLink = material.source_type === 'link';
  const externalUrl = isLink ? material.source_url : material.file;
  const openLabel = isLink ? t.materials.openInDrive : t.materials.openFile;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{material.title}</CardTitle>
        <CardDescription className='flex flex-wrap items-center gap-2'>
          <Badge variant='secondary'>
            {isLink ? t.materials.sourceType.link : t.materials.sourceType.file}
          </Badge>
          {material.course && (
            <Badge variant='outline'>
              {t.materials.courseLabel}: {material.course}
            </Badge>
          )}
        </CardDescription>
        {canManage && (
          <CardAction>
            <Button
              type='button'
              variant='destructive'
              size='icon-sm'
              aria-label={t.materials.delete}
              onClick={() => onDelete(material)}
            >
              <Icons.trash />
            </Button>
          </CardAction>
        )}
      </CardHeader>

      <CardContent className='flex flex-col gap-3'>
        {material.description && (
          <p className='text-muted-foreground text-sm whitespace-pre-line'>
            {material.description}
          </p>
        )}

        {isLink && material.embed_url && (
          <AspectRatio ratio={16 / 9} className='overflow-hidden rounded-lg ring-1 ring-foreground/10'>
            <iframe
              src={material.embed_url}
              title={material.title}
              loading='lazy'
              allowFullScreen
              referrerPolicy='no-referrer'
              sandbox='allow-scripts allow-popups allow-forms'
              className='absolute inset-0 size-full'
            />
          </AspectRatio>
        )}

        {externalUrl && (
          <div>
            <a
              href={externalUrl}
              target='_blank'
              rel='noopener noreferrer'
              className={buttonVariants({ variant: 'outline' })}
            >
              <Icons.externalLink data-icon='inline-start' />
              {openLabel}
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
