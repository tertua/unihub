# ADR-002: Frontend Mengonsumsi API Publik `/api/v1/`

**Status:** Accepted
**Date:** 2026-10-03

## Decision

Frontend aplikasi ini mengonsumsi API publik `/api/v1/` yang sama yang nanti
dibuka untuk integrasi sistem akademik (loose coupling, one-way integration,
app tidak pernah menulis ke SIAKAD). Endpoint API v1 tidak boleh dihapus
hanya karena "belum dipakai".

## Consequences

- Semua endpoint aplikasi hidup di bawah prefix `/api/v1/`.
- Frontend dev (`http://localhost:3000`) diizinkan lewat
  `CORS_ALLOWED_ORIGINS`.
- Kolom NIM/NIP pada `accounts.User` adalah bagian dari kontrak ini
  (pemetaan ke sistem akademik) dan tidak boleh dihapus.
