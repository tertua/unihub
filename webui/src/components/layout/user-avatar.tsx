'use client';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

/** Derives up to two uppercase initials from a display name / username. */
function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  const letters = parts.length === 1 ? parts[0].slice(0, 2) : parts[0][0] + parts[1][0];
  return letters.toUpperCase();
}

/**
 * Initials avatar for the signed-in user. Intentionally image-less: the
 * backend exposes no avatar URL, so we never fabricate one.
 */
export function UserAvatar({ name, className }: { name: string; className?: string }) {
  return (
    <Avatar className={cn('h-8 w-8 rounded-lg', className)}>
      <AvatarFallback className='rounded-lg text-xs font-medium'>{initials(name)}</AvatarFallback>
    </Avatar>
  );
}
