import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { ApiRequestError } from '@/lib/api-client';
import { en } from '@/i18n/en';
import { LocaleContext } from '@/i18n/locale-provider';
import { MaterialLinkForm } from '@/features/materials/components/material-link-form';
import { createLinkMaterial } from '@/features/materials/api/service';

// Mock the service seam, never `fetch` — components bypass api-client here.
vi.mock('@/features/materials/api/service', () => ({
  createLinkMaterial: vi.fn(),
  browseDrive: vi.fn()
}));

function renderWithProviders(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <LocaleContext.Provider value={{ locale: 'en', messages: en, setLocale: () => {} }}>
        {ui}
      </LocaleContext.Provider>
    </QueryClientProvider>
  );
}

describe('MaterialLinkForm server field errors', () => {
  beforeEach(() => {
    vi.mocked(createLinkMaterial).mockReset();
  });

  it('renders every field error key, including keys other than title/source_url', async () => {
    vi.mocked(createLinkMaterial).mockRejectedValue(
      new ApiRequestError(400, {
        file: ['Provide a file or a Drive link.'],
        description: ['Description is too long.'],
        detail: 'Bad request.'
      })
    );

    renderWithProviders(<MaterialLinkForm />);

    const form = document.querySelector('form');
    expect(form).not.toBeNull();

    const { getByLabelText, getByRole } = within(form as HTMLElement);
    fireEvent.change(getByLabelText(`${en.materials.form.titleLabel} *`), {
      target: { value: 'Week 1' }
    });
    fireEvent.change(getByLabelText(`${en.materials.form.urlLabel} *`), {
      target: { value: 'https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view' }
    });
    fireEvent.click(getByRole('button', { name: en.materials.form.submit }));

    await waitFor(() => {
      expect(createLinkMaterial).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(
        within(form as HTMLElement).getByText(/Provide a file or a Drive link\./)
      ).toBeInTheDocument();
    });
    expect(
      within(form as HTMLElement).getByText(`${en.materials.fieldLabels.file}:`)
    ).toBeInTheDocument();
    expect(
      within(form as HTMLElement).getByText(/Description is too long\./)
    ).toBeInTheDocument();
    expect(within(form as HTMLElement).getByText('Bad request.')).toBeInTheDocument();
  });
});
