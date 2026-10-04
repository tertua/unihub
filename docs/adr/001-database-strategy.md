# ADR-001: Database Strategy

**Status:** Accepted
**Date:** 2026-10-03

## Decision

PostgreSQL is used from the scaffolding phase onward because pgvector (a phase-2
RAG requirement) is only available on PostgreSQL. There is no SQLite fallback —
this avoids data migrations and SQL dialect differences later on.

## Consequences

- The engine in `DATABASES["default"]["ENGINE"]` is always
  `django.db.backends.postgresql`, read from the env vars
  (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
- The local database runs through `docker-compose.yml`
  (image `pgvector/pgvector:pg16`), so the `vector` extension is available
  without swapping the image when the RAG phase starts.
- Django tests create `test_<DB_NAME>` on the same server
  (the compose user is a superuser, so it automatically has the `CREATEDB`
  privilege).
