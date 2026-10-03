import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { en } from '@/i18n/en';
import { LocaleContext } from '@/i18n/locale-provider';
import type { Material, Paginated } from '@/features/materials/api/types';
import { MaterialList } from '@/features/materials/components/material-list';
import { listMaterials } from '@/features/materials/api/service';

vi.mock('@/features/materials/api/service', () => ({
  listMaterials: vi.fn(),
  deleteMaterial: vi.fn(),
  createLinkMaterial: vi.fn(),
  browseDrive: vi.fn()
}));

function sampleMaterial(id: number): Material {
  return {
    id,
    title: `Material ${id}`,
    description: '',
    course: 'CS101',
    file: null,
    source_url: 'https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view',
    drive_file_id: '1AbCdEfGhIjKlMnOpQrStUvWxYz012345',
    source_type: 'link',
    embed_url: null,
    drive_name: null,
    drive_mime_type: null,
    owner: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z'
  };
}

function pageOf(page: number, total: number, size = 20): Paginated<Material> {
  const start = (page - 1) * size;
  const count = Math.min(size, total - start);
  return {
    count: total,
    next: start + size < total ? `http://test/material/?page=${page + 1}` : null,
    previous: page > 1 ? `http://test/material/?page=${page - 1}` : null,
    results: Array.from({ length: count }, (_, index) => sampleMaterial(start + index + 1))
  };
}

function renderWithProviders(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <LocaleContext.Provider value={{ locale: 'en', messages: en, setLocale: () => {} }}>
        {ui}
      </LocaleContext.Provider>
    </QueryClientProvider>
  );
}

describe('MaterialList pagination', () => {
  beforeEach(() => {
    vi.mocked(listMaterials).mockReset();
  });

  it('shows page controls and "Page X of Y" derived from count', async () => {
    vi.mocked(listMaterials).mockImplementation(async (page = 1) => pageOf(page, 45));

    renderWithProviders(<MaterialList canManage={false} />);

    expect(await screen.findByText('Material 1')).toBeInTheDocument();
    expect(screen.getByText(en.materials.pagination.pageOf(1, 3))).toBeInTheDocument();
    expect(screen.getByRole('button', { name: en.materials.pagination.previous })).toBeDisabled();
    expect(screen.getByRole('button', { name: en.materials.pagination.next })).toBeEnabled();
  });

  it('advances by calling the service with page=2 and renders its data', async () => {
    vi.mocked(listMaterials).mockImplementation(async (page = 1) => pageOf(page, 45));

    renderWithProviders(<MaterialList canManage={false} />);

    await screen.findByText('Material 1');
    fireEvent.click(screen.getByRole('button', { name: en.materials.pagination.next }));

    expect(await screen.findByText('Material 21')).toBeInTheDocument();
    await waitFor(() => {
      expect(listMaterials).toHaveBeenCalledWith(2);
    });
    expect(screen.getByText(en.materials.pagination.pageOf(2, 3))).toBeInTheDocument();
  });
});
