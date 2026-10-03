# Faculty Learning Hub

Backend Django untuk aplikasi pembelajaran fakultas: **Material Hub**, **Tool Kit**,
**AI Chat** ( fase 2 ), dan **Space**. Repo ini adalah *MVP scaffolding* — struktur
project, konfigurasi, app `accounts` (lengkap), dan kerangka API `/api/v1/` —
plus `webui/`, App Shell Next.js yang mengonsumsi API tersebut.

> Keputusan arsitektur penting ada di [`docs/adr/`](docs/adr/):
> - [ADR-001 — Database Strategy (PostgreSQL sejak awal)](docs/adr/001-database-strategy.md)
> - [ADR-002 — Frontend mengonsumsi API publik `/api/v1/`](docs/adr/002-frontend-consumes-public-api.md)

## Stack

**Backend**

- Python 3.12, Django 5+/6, Django REST Framework
- JWT (`djangorestframework-simplejwt`), CORS (`django-cors-headers`)
- OpenAPI: `drf-spectacular`
- PostgreSQL 16+ dengan **pgvector** (via image `pgvector/pgvector:pg16`)

**Web UI (`webui/`)**

- Next.js 16 (App Router), React 19, TypeScript
- Tailwind CSS v4 + shadcn/ui (Base UI primitives)
- TanStack Query, Zod, TanStack Form
- Package manager: [Bun](https://bun.sh)

## Versi

Proyek memakai **SemVer** (`MAJOR.MINOR.PATCH`) dan **mulai dari `0.1.0`**.
Selama di `0.x`: `MINOR` untuk fitur/milestone, `PATCH` untuk perbaikan.
Versi rilis ditandai tag `vX.Y.Z` di `master`, dan angka di `webui/package.json`
mengikuti versi rilis terakhir.

**Versi hanya naik ketika Anda meminta rilis.** Agent menghitung angka
berikutnya dari commit sejak tag terakhir (ada fitur → `MINOR`, hanya
perbaikan → `PATCH`), lalu mengeksekusi urutan rilisnya. Di antara rilis versi
diam — agent hanya boleh *menyarankan* rilis saat milestone selesai, tidak
pernah menaikkan sendiri. **Bagian `MAJOR` tidak pernah diubah tanpa
instruksi eksplisit Anda** — kenaikan ke `1.0.0` hanya saat Anda menyatakan
produk sudah stabil. (Ketentuan lengkap untuk agent ada di `AGENTS.md` §10.)

## Instalasi (environment bersih)

```bash
# 1. Database PostgreSQL
cp .env.example .env
docker compose up -d db

# 2. Virtualenv + dependencies
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Migrasi + akun admin
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser

# 4. Jalankan
.venv/bin/python manage.py runserver
```

Buka:

| URL | Isi |
| --- | --- |
| <http://127.0.0.1:8000/admin/> | Django admin |
| <http://127.0.0.1:8000/api/docs/> | Swagger UI |
| <http://127.0.0.1:8000/api/schema/> | OpenAPI schema (YAML) |

## Konfigurasi database (env)

Semua konfigurasi dibaca dari `.env` (salin dari `.env.example`).
**Tidak ada fallback SQLite** — engine selalu `django.db.backends.postgresql`
lihat [ADR-001](docs/adr/001-database-strategy.md).

| Variabel | Default | Keterangan |
| --- | --- | --- |
| `DB_NAME` | `faculty_hub` | Nama database (dibuat `POSTGRES_DB` di compose) |
| `DB_USER` | `postgres` | User database |
| `DB_PASSWORD` | `postgres` | Password database |
| `DB_HOST` | `localhost` | Host database |
| `DB_PORT` | `5432` | Port database |
| `SECRET_KEY` | *(wajib diisi)* | Django secret key |
| `DEBUG` | `False` | `True` hanya untuk local dev |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Dipisah koma |

Database test dibuat otomatis sebagai `test_<DB_NAME>` (user compose adalah
superuser, jadi punya izin `CREATEDB`).

Contoh memakai database di luar docker:

```env
DB_HOST=192.168.2.2
DB_PORT=5432
DB_PASSWORD=***
```

## Endpoint API v1

Prefix: `/api/v1/` — konsumsi publik frontend & integrasi, lihat
[ADR-002](docs/adr/002-frontend-consumes-public-api.md).

| Method | Endpoint | Auth | Keterangan |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register/` | Public | Register; `role` hanya `student`/`lecturer` |
| `POST` | `/api/v1/auth/token/` | Public | Login → `{access, refresh}` |
| `POST` | `/api/v1/auth/token/refresh/` | Public | Refresh → `{access}` |
| `GET` | `/api/v1/auth/me/` | JWT | Profil user sedang login |
| `PATCH` | `/api/v1/auth/me/` | JWT | Update profil (identity field read-only) |

Contoh:

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/v1/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"...","role":"student","student_id_number":"2026001"}'

# Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"..."}'

# Profil
curl http://127.0.0.1:8000/api/v1/auth/me/ -H "Authorization: Bearer <access>"
```

Response default memakai pagination (`page_size = 20`); autentikasi JWT;
permission default `IsAuthenticated`.

## Test

```bash
.venv/bin/python manage.py test
```

Menjalankan unit test endpoint auth (register, login, refresh, me termasuk
sisi unauthorized). Test DB `test_faculty_hub` dibuat & dihancurkan otomatis
di PostgreSQL.

## Web UI

`webui/` adalah App Shell Next.js: login/register, proteksi route, profil,
navigasi 4 komponen produk (Overview, Material Hub, Tool Kit, AI Chat, Space).
Semua data diambil dari `/api/v1/` — **tidak ada mock data** di dalamnya;
halaman yang endpoint-nya belum ada menampilkan *empty state* yang jujur.

```bash
# 1. Jalankan backend dulu (port 8000)
.venv/bin/python manage.py runserver 127.0.0.1:8000

# 2. Jalankan webui (port 3000)
cd webui
bun install
cp env.example.txt .env.local     # isi NEXT_PUBLIC_API_URL
bun run dev
```

Buka **<http://localhost:3000>** — harus `localhost`, bukan `127.0.0.1`,
karena CORS backend hanya mengizinkan `http://localhost:3000`.

| Variabel | Nilai dev | Keterangan |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Base URL API. **Wajib rebuild** bila diubah (env dibaca saat build) |

Script yang tersedia: `bun run dev`, `bun run build`, `bun run start`,
`bun run typecheck`, `bun run lint`, `bun run format`.

### Autentikasi di webui

- Login/register memanggil `POST /api/v1/auth/token/` dan
  `POST /api/v1/auth/register/`.
- Token disimpan sebagai cookie **non-httpOnly** `fh_access` / `fh_refresh`,
  dan sekaligus dikirim sebagai header `Authorization: Bearer` oleh
  `src/lib/api-client.ts` — backend tidak diubah sama sekali.
- `src/proxy.ts` (middleware Next.js) menjaga route `/dashboard/*` di sisi
  server, sehingga `dashboard/layout.tsx` tetap komponen server.

### Bahasa (i18n)

UI tersedia dalam **2 bahasa: Inggris (default) dan Indonesia**, tanpa library
tambahan. Semua copy user-facing ada di catalog string `webui/src/i18n/`:

- `en.ts` — sumber kebenaran (type `Messages` diturunkan dari sini)
- `id.ts` — terjemahan Indonesia, wajib cocok key-per-key (dicek TypeScript)
- pemilih bahasa: toggle **EN / ID** di header; pilihan disimpan di cookie
  non-httpOnly `fh_locale`, komponen server membaca lewat `getMessages()`
  dan komponen client lewat hook `useMessages()`.

### Struktur webui

```
webui/src/
├── app/            # App Router: /auth/*, /dashboard/*
├── features/auth/  # login, register, session, service API
├── components/     # layout (sidebar/header/nav), ui (shadcn), not-implemented
├── config/         # nav-config (menu 4 komponen produk)
├── i18n/           # catalog EN + ID, locale provider, hook
├── lib/            # api-client (fetch + refresh token otomatis)
├── hooks/          # use-nav, use-mobile, use-session
└── proxy.ts        # middleware: guard /dashboard/*
```

### Asal-usul `webui/`

Bukan ditulis dari nol — App Shell diawali dari template MIT:

- Upstream: `https://github.com/Kiranism/next-shadcn-dashboard-starter.git`
- Base commit: `7705dfc0d13889e45c26a55ad5908da6a7a9a605`
  (`chore(deps): upgrade @clerk/nextjs 7.3.5 → 7.8.1`)
- Lisensi sumber tetap berlaku: lihat `webui/LICENSE` (MIT, © Kiranism).
- `webui/.git` dihapus supaya project jadi **satu repo** tunggal di root ini.
  Konsekuensinya: riwayat upstream tidak bisa lagi di-`pull`, dan rollback
  lokal baru tersedia setelah commit pertama repo ini.

Seluruh kode template yang tidak dipakai (Clerk, Sentry, AI SDK, Kanban,
Notifications, mock/contoh features, skrip `cleanup`, docs template, berkas
`.agents/`/`.claude/`, dan berkas Docker template — `Dockerfile`,
`Dockerfile.bun`, `.dockerignore` yang tidak direferensikan compose mana pun)
sudah dihapus; yang tersisa tinggal App Shell yang memanggil API kita.
Konfigurasi Docker untuk deploy akan dibuat terintegrasi di
`docker-compose.yml` root pada fase deployment — bukan terpisah di dalam
`webui/`. `output: 'standalone'` di `next.config` tetap aktif lewat
`BUILD_STANDALONE` sebagai bekalnya.

## Struktur project

```
.
├── config/                 # settings, urls, wsgi/asgi
├── accounts/               # User custom (role, NIM, NIP, study_program) + auth API
├── materials/              # scaffold — Material Hub (fase berikutnya)
├── tools/                  # scaffold — Tool Kit
├── chat/                   # scaffold — AI Chat (fase 2, RAG)
├── spaces/                 # scaffold — Space (membership & forum)
├── webui/                  # App Shell Next.js (lihat bagian "Web UI")
├── docs/adr/               # Architecture Decision Records
├── thoughts/               # rencana kerja & provenance
├── docker-compose.yml      # PostgreSQL + pgvector
├── requirements.txt
├── .env.example            # template konfigurasi
└── manage.py
```

## Catatan: bytecode cache

Bytecode Python dikumpulkan terpusat di `.cache/python/` (sudah di-`.gitignore`)
supaya folder `__pycache__/` tidak bertebaran di repo. `manage.py`,
`config/asgi.py`, dan `config/wsgi.py` menyetel `PYTHONPYCACHEPREFIX` sebelum
Django di-import. Bila menjalankan Python langsung (di luar entrypoint itu),
export dulu:

```bash
export PYTHONPYCACHEPREFIX="$PWD/.cache/python"
```
