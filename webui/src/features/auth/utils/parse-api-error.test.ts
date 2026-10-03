import { describe, expect, it } from 'vitest';
import { ApiRequestError } from '@/lib/api-client';
import { en } from '@/i18n/en';
import { id } from '@/i18n/id';
import { parseApiError } from '@/features/auth/utils/parse-api-error';

describe('parseApiError', () => {
  it('defaults a 401 to the sign-in "incorrect credentials" copy', () => {
    const result = parseApiError(new ApiRequestError(401, { detail: 'no' }), en.errors);

    expect(result).toEqual({
      fieldErrors: {},
      formError: en.errors.incorrectCredentials
    });
  });

  it('renders the session-expired copy for a 401 in the generic context', () => {
    const result = parseApiError(
      new ApiRequestError(401, { detail: 'no' }),
      en.errors,
      'generic'
    );

    expect(result.formError).toBe(en.errors.sessionExpired);
  });

  it('keeps sign-in copy for an explicit auth context', () => {
    const result = parseApiError(
      new ApiRequestError(401, { detail: 'no' }),
      id.errors,
      'auth'
    );

    expect(result.formError).toBe(id.errors.incorrectCredentials);
  });

  it('maps a non-ApiRequestError to the unreachable copy', () => {
    const result = parseApiError(new Error('boom'), en.errors);

    expect(result).toEqual({ fieldErrors: {}, formError: en.errors.unreachable });
  });

  it('splits a 400 field body into fieldErrors and formError', () => {
    const result = parseApiError(
      new ApiRequestError(400, {
        title: ['Title must not be blank.'],
        detail: 'Bad request.'
      }),
      en.errors
    );

    expect(result.fieldErrors).toEqual({ title: ['Title must not be blank.'] });
    expect(result.formError).toBe('Bad request.');
  });
});
