# AGENTS.md — Instructions for AI Agents

Working instructions for any AI agent (or human) modifying this repository.
Read this file before touching code.

---

## 1. Non-negotiable language rules

1. **English only in code.** Identifiers, comments, docstrings, log lines, error
   messages, validation messages, enum labels, and user-facing UI copy must all
   be English.
   - `# Keep bytecode out of the repo` — OK.
   - `# Supaya tidak ada __pycache__` — forbidden.
2. **English only in commit messages.** Subject line format:
   `type(scope): description` (e.g. `feat(accounts): add password reset endpoint`).
   Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
3. **English in code reviews, plan files, and agent handoffs.** Prose documents
   that a human reads in Indonesian (task briefs) are the only exception; the
   source of truth for agents is always this file and the English docs.
4. **English in every subagent exchange.** Task prompts, subagent descriptions,
   tool arguments, and returned reports are English. Never emit Chinese
   characters (or any other non-English script) in agent traffic — it breaks
   reviewability and violates rule 1 downstream.
5. When you find Indonesian text inside a source file, **translate it to English
   and mention it in your report.** Do not leave it.
   - Single sanctioned exception: `webui/src/i18n/id.ts`, the Indonesian string
     catalog, which exists precisely to hold Indonesian UI copy.
6. **Chat replies to the operator are in Indonesian.** The final message shown
   in the chat window is written in Bahasa Indonesia. Everything that persists
   — code, comments, commit messages, docs, plan files, subagent prompts —
   stays English per rules 1–4.
7. **`README.md` and other human-facing docs are written in natural
   Indonesian; `AGENTS.md` and every agent-facing doc are English-only.** The
   operator reads the README; agents read this file.

Verify at any time:

```bash
grep -rniE 'wajib|belum|tidak|harus|untuk|dengan|yang|punya akun|halaman ini' \
  --include='*.py' --include='*.ts' --include='*.tsx' --exclude-dir=i18n \
  accounts config webui/src
# expected: no output (the only Indonesian lives in webui/src/i18n/id.ts)
```

---

## 2. What this project is

**Faculty Learning Hub** — a faculty learning platform with four product
components: **Material Hub**, **Tool Kit**, **AI Chat** (phase 2, RAG), and
**Space**.

Current state (MVP):

| Part | State |
| --- | --- |
| Django backend + `/api/v1/` auth API | complete |
| `accounts` app (custom user, roles, NIM/NIP) | complete |
| `materials` app (models, API, tests) | implemented — Material Hub API |
| `tools`, `chat`, `spaces` apps | scaffold only (empty packages) |
| `webui/` App Shell (Next.js) | complete, wired to real JWT API |
| Material upload (Material Hub API) | **implemented** — `materials` app, `/api/v1/material/` |
| RAG chat, spaces | **future phases — do not build them now** |

Architecture decisions are mandatory reading:

- [`docs/adr/001-database-strategy.md`](docs/adr/001-database-strategy.md) —
  PostgreSQL from day one, **never SQLite**.
- [`docs/adr/002-frontend-consumes-public-api.md`](docs/adr/002-frontend-consumes-public-api.md) —
  the frontend and every integration talk to the **same public `/api/v1/`**.

---

## 3. Repository layout

```
.
├── config/            # Django settings, urls, wsgi/asgi
├── accounts/          # Custom User (role, NIM, NIP, study_program) + auth API
├── materials/ tools/ chat/ spaces/   # scaffolds for later phases
├── webui/             # Next.js 16 App Shell (bun)
├── docs/adr/          # Architecture Decision Records
├── thoughts/          # plans and continuity ledgers (gitignored)
├── docker-compose.yml # PostgreSQL + pgvector
├── requirements.txt
├── .env               # local config — gitignored, never commit
├── .env.example       # tracked template
└── manage.py
```

`webui/src` layout:

```
app/            # App Router: /auth/sign-in, /auth/sign-up, /dashboard/*
features/auth/  # sign-in/sign-up forms, session hook, API service
components/     # layout (sidebar/header/nav), ui (shadcn), not-implemented
config/         # nav-config — the four product components
i18n/           # en.ts + id.ts string catalogs, locale provider, useMessages()
lib/            # api-client — fetch + automatic token refresh
hooks/          # use-nav, use-mobile, use-session
proxy.ts        # Next middleware guarding /dashboard/*
```

---

## 4. Commands

### Backend (Django)

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8000   # dev server
.venv/bin/python manage.py test                        # 17 tests, must stay green
.venv/bin/python manage.py check                       # 0 issues
.venv/bin/python manage.py makemigrations --check       # must report no changes
.venv/bin/python manage.py spectacular --validate        # OpenAPI schema valid
```

### Frontend (`webui/`)

```bash
cd webui
bun install          # never npm/yarn — bun.lock is the lockfile
bun run typecheck    # tsc --noEmit, exit 0
bun run lint         # oxlint, 0 warnings 0 errors
bun run build        # next build, exit 0
bun run dev          # http://localhost:3000
```

**Run the app at `http://localhost:3000`, not `127.0.0.1:3000`** — CORS on the
backend allows only `http://localhost:3000`.

Environment variables for `webui` live in `webui/.env.local` (gitignored):

| Variable | Dev value | Note |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | inlined at build time; changing it requires a rebuild |

---

## 5. API contract (`/api/v1/auth/`)

These endpoints are an **INTEGRATION CONTRACT**. Never delete, rename, or change
their request/response shape for internal convenience.

| Method | Endpoint | Auth | Notes |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register/` | public | `role` accepts only `student` / `lecturer`; payload may include `student_id_number`, `study_program` |
| `POST` | `/api/v1/auth/token/` | public | returns `{access, refresh}`; 401 on bad credentials |
| `POST` | `/api/v1/auth/token/refresh/` | public | payload `{refresh}` → `{access}`; 401 when invalid |
| `GET` | `/api/v1/auth/me/` | JWT Bearer | current profile |
| `PATCH` | `/api/v1/auth/me/` | JWT Bearer | `role`, `username`, `student_id_number`, `lecturer_id_number` are read-only |

Also protected by the contract:

- The model columns `student_id_number` and `lecturer_id_number` are **nullable
  on purpose** (`INTEGRATION CONTRACT`). Never drop or make them required.
- `CORS_ALLOWED_ORIGINS` must keep `http://localhost:3000`.

**URL naming rule:** resource segments are always **singular, never plural** —
`/api/v1/invoice/`, never `/api/v1/invoices/`. Verb and field segments stay
plain (`register`, `token`, `refresh`, `me`). This applies to every endpoint,
present and future.

---

## 6. Backend conventions

- **Validation lives in serializers**, never in views. Views stay thin.
- **Pure Django ORM only.** No `raw()`, no `extra()`, no `RawSQL`, no
  `cursor.execute()` — portability with PostgreSQL and pgvector later.
- **English comments only, short, explaining "why" not "what".**
- `AUTH_USER_MODEL = "accounts.User"` must be declared before the first
  migration; never replace the user model.
- `User.save()` forces superusers to `role=admin`. Keep this invariant — it stops
  role-based checks from locking Django's own superuser out.
- Default permission is `IsAuthenticated`; open a view explicitly with
  `AllowAny` only when registration or token endpoints require it.
- Bytecode is centralized in `.cache/python/` (gitignored). Entry points set
  `PYTHONPYCACHEPREFIX` **before** Django is imported — do not add new
  `__pycache__` folders.
- New endpoints go under `config/urls.py` → `api/v1/`, with a serializer, tests,
  and a `@extend_schema`/serializer docstring so the OpenAPI schema stays useful.
- **Singular resource paths only.** Use `/api/v1/material/`, `/api/v1/invoice/`,
  `/api/v1/space/` — never the plural form. Same rule for router prefixes and
  `router.register()` arguments (`r"material"`, not `r"materials"`). Named
  endpoints keep their action/field names (`register/`, `token/`, `me/`).

---

## 7. Frontend conventions

- **Zero mock data.** No faker, no `constants/` sample arrays, no hardcoded
  fake metrics, no placeholder people. Every value comes from `/api/v1/`.
- **Unused components are not leftovers.** `components/ui/`, `components/forms/`,
  `ui/table/`, the icon registry, and small helper hooks form the project's
  design contract — like the API contract, they exist whether or not a page
  consumes them yet. Never delete a component because nothing imports it
  today: the owner picks the visuals, so re-designing it yourself will not
  match. Removing any of it requires an explicit instruction.
- If an endpoint does not exist yet, render an honest empty state via
  `components/not-implemented.tsx`. Never fake content to fill space.
- All requests go through `lib/api-client.ts` (adds `Authorization: Bearer`,
  refreshes an expired access token, reads `fh_access` / `fh_refresh` cookies).
  Never call `fetch()` directly from components.
- The frontend adapts to the backend. **Never change the backend to fit the
  frontend.**
- Route guarding happens in `src/proxy.ts` (middleware) so server components
  stay server components. Keep `dashboard/layout.tsx` free of client-side auth
  logic.
- **All UI copy lives in the string catalog `src/i18n/`** (English `en.ts` is
  the source of truth; `id.ts` mirrors it key-for-key and is the only file
  allowed to contain Indonesian). Client components use `useMessages()`,
  server components `await getMessages()`; the active locale is the
  `fh_locale` cookie with a switch in the header. Never hardcode a user-facing
  sentence inside a component, and always add a key to **both** catalogs.
- No Clerk, no Sentry, no AI SDK, no kanban, no notifications, no new
  dependencies without explicit approval.

---

## 8. Scope discipline

- Build only what the current task asks for. No speculative endpoints, hooks,
  components, or "while I'm here" refactors.
- Do not add features from the template's origin (the upstream dashboard starter
  was stripped on purpose).
- Record the origin of `webui/` in `README.md` → *Asal-usul `webui/`*; it stays
  MIT-licensed under `webui/LICENSE`.

---

## 9. Secrets and configuration

- `.env` and `webui/.env.local` are **gitignored and must stay that way**.
  Never copy real credentials into tracked files.
- `.env.example` carries only placeholders.
- Never hardcode database passwords, `SECRET_KEY`, or admin passwords in source.

---

## 10. Git workflow

- **Two branches — this model is fixed:**
  - `master` = release only. **Never commit to it directly.** It advances
    solely by fast-forward promotion from `dev` when the operator asks for a
    release: `git switch master && git merge --ff-only dev`.
  - `dev` = the working branch. Every agent commit, feature branch, and
    Dependabot PR lands here; feature branches fork from `dev` and merge back
    into `dev`.
  - No merge commits, no force-push. Dependabot's `target-branch`
    (`.github/dependabot.yml`) must stay `dev` so release PRs never arrive
    on `master` by accident.
- **Versioning — SemVer, starts at `0.1.0`:**
  - The release version lives as an annotated tag `vX.Y.Z` on `master`;
    `webui/package.json` `"version"` must equal the released version.
  - While on `0.x`: `MINOR` carries features and milestones, `PATCH` carries
    fixes. Versions change **only when the operator asks for a release** —
    never inside feature commits, never after Dependabot merges, never
    proactively. The agent may *propose* a release once a milestone is done
    and the DoD is green, but never bumps alone.
  - **The agent computes the next number** from the commits since the last
    tag: any `feat` -> `MINOR` +1, otherwise `PATCH` +1. A breaking change
    means a `MAJOR` proposal: stop and wait for the operator's explicit yes.
  - Release sequence: bump `webui/package.json` on `dev` -> commit
    `chore(release): bump to vX.Y.Z` -> push -> ff-promote `master` ->
    annotated tag `vX.Y.Z` on `master` -> push the tag.
  - **Never bump `MAJOR` without an explicit operator instruction.**
    `1.0.0` is declared only when the operator states the product is stable.
- **Never commit or push without explicit instruction.** Stage, show the diff or
  `git status`, then wait.
- Stage only what the task touched. Never `git add -f`; if a path is gitignored,
  leave it alone.
- Commit message: `type(scope): lowercase description`, English, imperative
  mood, one line for the subject; reference the plan file in the body when a
  plan exists.
- **Agent commit trailer:** every agent-made commit ends with the trailer
  `Co-authored-by: <model> <noreply@opencode.ai>` as the last paragraph of
  the message, where `<model>` is the model that actually produced the
  change — read it from your own system context (e.g.
  `mimo-v2.6-flash-free`, `claude-sonnet-4-5`); never guess, never use
  another identity. Human commits omit the trailer. The email part stays
  constant so agent work remains greppable across models:
  `git log --grep noreply@opencode.ai`.
- **Commit execution:** local commit+push runs through the `committer`
  subagent (`.opencode/agents/committer.md`) when the operator mentions it.
  Every other agent stages its work, shows `git diff --cached`, and waits —
  the operator's mention of `committer` is the explicit instruction required
  by §10's first rule.
- Before committing: `git status`, `git diff`, and `git log --oneline -10`.
- This repository has **one `.git`, at the repository root.** Do not
  `git init` inside `webui/` — its nested `.git` was removed deliberately.

---

## 11. Definition of done

A change is finished only when all of these pass:

```bash
# backend
.venv/bin/python manage.py test
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check
.venv/bin/python manage.py spectacular --validate

# frontend
cd webui && bun run typecheck && bun run lint && bun run build

# language audit (must produce no output; i18n/ holds the sanctioned id.ts)
grep -rniE 'wajib|belum|tidak|harus|untuk|dengan|yang' \
  --include='*.py' --include='*.ts' --include='*.tsx' --exclude-dir=i18n \
  accounts config webui/src

# no mock data / no template leftovers
grep -rniE 'faker|mockData|clerk|sentry' accounts config webui/src
```

Report honestly: state what you verified, what you could not verify, and any
decision that needs a human's sign-off. Do not claim a check passed if it did
not run.
