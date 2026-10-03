# ADR-003: Google Shared Drive Storage

**Status:** Accepted
**Date:** 2026-10-03
**Supersedes:** the local-disk storage assumption in the Material Hub plan.

## Decision

Material files are stored in the operator's paid Google Workspace **Shared
Drive** through a custom Django `Storage` backend (`materials/storage.py`) using
a **service account** (OAuth2 JWT-bearer, RS256). The stored file name is the
Drive file ID.

## Context

The operator owns a paid Google Workspace Shared Drive and no longer provisions
local disk for new uploads ("repot menyediakan source untuk penyimpanan"). All
new material uploads therefore target the Shared Drive instead of local disk.

## Browse access (rev.3)

The in-app Drive browser (`GET /api/v1/drive/`) reads the Shared Drive tree for
any authenticated user because it derives its access from the **same
service-account membership** in the operator's Shared Drive — no per-user OAuth,
no additional consent. It only ever *reads*: it never mutates Drive and never
creates a material.

## Configuration

- `GOOGLE_DRIVE_SERVICE_ACCOUNT_B64` — base64-encoded service-account JSON key.
- `GOOGLE_DRIVE_SHARED_DRIVE_ID` — the Shared Drive id (for `supportsAllDrives`/
  `driveId`-aware API calls).
- `GOOGLE_DRIVE_FOLDER_ID` — the target folder for uploads inside the Shared Drive.
- `GOOGLE_DRIVE_API_KEY` — optional; enables metadata enrichment only.

When unset, `STORAGES["default"]` falls back to `FileSystemStorage`: there is
**zero fallback to Drive when unconfigured**, and dev/test stay zero-network.

## Consequences

- **Resumable upload is required.** Drive's simple/multipart upload caps at
  5 MB; the validated max is 20 MB (`MAX_UPLOAD_SIZE_BYTES`), so the save path
  uses a resumable session (initiate → `PUT` the bytes → finalise).
- Uploads use only the Python stdlib (`urllib.request`); the only added
  dependencies are `PyJWT` and `cryptography`.
- `GoogleDriveStorage.open()`/`size()` raise `NotImplementedError` by design:
  nothing in the API or admin reads bytes back — files open from Drive directly
  in the browser. `exists()` returns `False` (write-only use; avoids a
  per-call network hit).
- **Ops note (outside code):** for students to open/embed these files, the
  operator must set the Shared Drive/file sharing policy (e.g. "anyone in the
  org with the link can view", or domain-wide). **Code cannot do this.**
- ADR-001 (PostgreSQL) is unaffected.
