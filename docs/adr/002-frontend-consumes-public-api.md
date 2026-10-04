# ADR-002: Frontend Consumes the Public API `/api/v1/`

**Status:** Accepted
**Date:** 2026-10-03

## Decision

This application's frontend consumes the same public `/api/v1/` API that will
later be opened to academic-system integrations (loose coupling, one-way
integration; the app never writes to SIAKAD). API v1 endpoints must not be
deleted just because they are "not used yet".

## Consequences

- Every application endpoint lives under the `/api/v1/` prefix.
- The dev frontend (`http://localhost:3000`) is allowed via
  `CORS_ALLOWED_ORIGINS`.
- The NIM/NIP columns on `accounts.User` are part of this contract
  (mapping to the academic system) and must not be removed.
