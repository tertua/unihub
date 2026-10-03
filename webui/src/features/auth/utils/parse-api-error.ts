import { ApiRequestError } from '@/lib/api-client';
import { en, type Messages } from '@/i18n/en';

/** Per-field validation errors returned by DRF as `{ field: ["msg", ...] }`. */
export type FieldErrors = Record<string, string[]>;

/**
 * Which copy a 401 should render. `'auth'` (default) is the sign-in form's
 * "incorrect credentials"; `'generic'` is for authenticated screens where a
 * 401 means the session expired, not a bad password.
 */
export type ApiErrorContext = 'auth' | 'generic';

/**
 * Normalises a caught API error into `{ fieldErrors, formError }`.
 * DRF field errors surface per input; anything else becomes a form-level
 * message. `messages` is the active locale's error catalog — callers pass it
 * so the user never sees a mixed-language form. `context` only changes the
 * 401 copy; the default preserves the sign-in/sign-up behaviour exactly.
 */
export function parseApiError(
  error: unknown,
  messages: Messages['errors'] = en.errors,
  context: ApiErrorContext = 'auth'
): {
  fieldErrors: FieldErrors;
  formError: string | null;
} {
  if (error instanceof ApiRequestError) {
    const body = error.body;

    if (error.status === 400 && body && typeof body === 'object' && !Array.isArray(body)) {
      const fieldErrors: FieldErrors = {};
      let formError: string | null = null;

      for (const [key, value] of Object.entries(body as Record<string, unknown>)) {
        const msgs = Array.isArray(value) ? value.map(String) : [String(value)];
        if (key === 'detail' || key === 'non_field_errors') {
          formError = msgs.join(' ');
        } else {
          fieldErrors[key] = msgs;
        }
      }
      return { fieldErrors, formError };
    }

    if (error.status === 401) {
      return {
        fieldErrors: {},
        formError: context === 'generic' ? messages.sessionExpired : messages.incorrectCredentials
      };
    }

    const detail =
      body && typeof body === 'object' && 'detail' in body
        ? String((body as { detail: unknown }).detail)
        : null;
    return { fieldErrors: {}, formError: detail ?? messages.generic };
  }

  return { fieldErrors: {}, formError: messages.unreachable };
}
