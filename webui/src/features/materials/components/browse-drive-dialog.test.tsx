import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiRequestError } from '@/lib/api-client';
import { en } from '@/i18n/en';
import { LocaleContext } from '@/i18n/locale-provider';
import type { DriveBrowseResponse } from '@/features/materials/api/types';
import { BrowseDriveDialog } from '@/features/materials/components/browse-drive-dialog';
import { browseDrive } from '@/features/materials/api/service';

vi.mock('@/features/materials/api/service', () => ({
  browseDrive: vi.fn(),
  listMaterials: vi.fn(),
  deleteMaterial: vi.fn(),
  createLinkMaterial: vi.fn()
}));

function renderDialog() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <LocaleContext.Provider value={{ locale: 'en', messages: en, setLocale: () => {} }}>
        <BrowseDriveDialog open onOpenChange={() => {}} onSelect={() => {}} />
      </LocaleContext.Provider>
    </QueryClientProvider>
  );
}

describe('BrowseDriveDialog status handling', () => {
  beforeEach(() => {
    vi.mocked(browseDrive).mockReset();
  });

  it('renders the unconfigured copy on a 503', async () => {
    vi.mocked(browseDrive).mockRejectedValue(new ApiRequestError(503, { detail: 'no' }));

    renderDialog();

    expect(await screen.findByText(en.materials.browse.unavailable)).toBeInTheDocument();
  });

  it('renders the Drive-API-error copy on a 502', async () => {
    vi.mocked(browseDrive).mockRejectedValue(new ApiRequestError(502, { detail: 'no' }));

    renderDialog();

    expect(await screen.findByText(en.materials.browse.errorServer)).toBeInTheDocument();
  });

  it('renders the unconfigured copy when the body reports configured: false', async () => {
    vi.mocked(browseDrive).mockResolvedValue({
      configured: false,
      parent: null,
      results: [],
      truncated: false
    } satisfies DriveBrowseResponse);

    renderDialog();

    expect(await screen.findByText(en.materials.browse.unavailable)).toBeInTheDocument();
  });

  it('renders the folder listing on a normal response', async () => {
    vi.mocked(browseDrive).mockResolvedValue({
      configured: true,
      parent: null,
      results: [
        {
          id: 'fileXyz0123456789',
          name: 'week1.pdf',
          mimeType: 'application/pdf',
          isFolder: false,
          url: 'https://drive.google.com/file/d/fileXyz0123456789/view'
        }
      ],
      truncated: false
    } satisfies DriveBrowseResponse);

    renderDialog();

    expect(await screen.findByText('week1.pdf')).toBeInTheDocument();
    await waitFor(() => {
      expect(browseDrive).toHaveBeenCalled();
    });
  });
});
