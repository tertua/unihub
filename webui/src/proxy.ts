import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Guard for `/dashboard/*`.
 *
 * Presence-only check: the JWT is opaque to the edge runtime here, so real
 * validation happens on the backend for every API call. This only prevents
 * rendering the shell for visitors with no token at all.
 */
export function proxy(req: NextRequest) {
  const hasSession = req.cookies.has('fh_access');

  if (!hasSession && req.nextUrl.pathname.startsWith('/dashboard')) {
    const signInUrl = new URL('/auth/sign-in', req.url);
    return NextResponse.redirect(signInUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)'
  ]
};
