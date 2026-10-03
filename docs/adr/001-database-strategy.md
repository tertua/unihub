# ADR-001: Database Strategy

**Status:** Accepted
**Date:** 2026-10-03

## Decision

PostgreSQL dipakai sejak fase scaffolding karena pgvector (kebutuhan RAG fase 2)
hanya tersedia di PostgreSQL. Tidak ada fallback SQLite — ini menghindari migrasi
data dan perbedaan dialek SQL di kemudian hari.

## Consequences

- Engine `DATABASES["default"]["ENGINE"]` selalu
  `django.db.backends.postgresql`, dibaca dari env vars
  (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
- Database lokal dijalankan lewat `docker-compose.yml`
  (image `pgvector/pgvector:pg16`), sehingga ekstensi `vector` tersedia
  tanpa mengganti image saat fase RAG dimulai.
- Test Django membuat `test_<DB_NAME>` di server yang sama
  (user compose adalah superuser, jadi otomatis punya izin `CREATEDB`).
