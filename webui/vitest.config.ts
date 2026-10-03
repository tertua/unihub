import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

/**
 * Vitest configuration for the App Shell's unit/component tests.
 *
 * Mirrors the `@/*` path alias from `tsconfig.json` and runs in jsdom so
 * Testing Library can drive real React components. Tests are co-located with
 * the code under test as `*.test.ts(x)`.
 */
export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}']
  }
});
