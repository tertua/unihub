import { describe, expect, it } from 'vitest';
import { en } from '@/i18n/en';
import { id } from '@/i18n/id';

/** Recursively collect dotted key paths; function values are compared by presence. */
function collectKeys(value: unknown, prefix = ''): Set<string> {
  const keys = new Set<string>();
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    for (const [key, child] of Object.entries(value)) {
      const path = prefix ? `${prefix}.${key}` : key;
      keys.add(path);
      for (const nested of collectKeys(child, path)) keys.add(nested);
    }
  }
  return keys;
}

describe('i18n key parity', () => {
  it('id mirrors every en key', () => {
    const enKeys = collectKeys(en);
    const idKeys = collectKeys(id);

    const missing = [...enKeys].filter((key) => !idKeys.has(key)).toSorted();
    const extra = [...idKeys].filter((key) => !enKeys.has(key)).toSorted();

    expect(missing).toEqual([]);
    expect(extra).toEqual([]);
  });
});
