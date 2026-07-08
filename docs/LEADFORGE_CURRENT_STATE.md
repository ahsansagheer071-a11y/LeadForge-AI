# LeadForge AI — Current State Report

> Authoritative project handoff. Generated 2026-07-08.
> Branch: `stabilization/repository-audit` (based on `main@f46dd57`)

---

## 1. Product Purpose

LeadForge AI is a lead-to-sale AI website generation platform. It discovers local businesses, analyzes their websites via AI, generates replacement websites, packages them for deployment, and produces personalized outreach emails containing preview links.

It is **not** a generic website builder. The entire pipeline is lead-specific.

---

## 2. Correct Lead-to-Sale Workflow

```
Lead Discovery / Lead Creation
  → Website Screenshot (Playwright → Cloudinary)
  → Website Analysis (scraper extracts meta, tech, structure)
  → AI Audit & Score (Groq → Pollinations → NVIDIA fallback)
  → AI Website Generation (static HTML via AI provider)
  → Persistent Preview (DB-stored iframe-ready HTML)
  → Deployment ZIP Package (downloadable)
  → Outreach Email with Preview Link (AI-generated templates)
  → Lead Conversion
```

---

## 3. Current Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Backend | Python / FastAPI | 3.14 / 0.138.0 |
| ASGI | Uvicorn + Gunicorn | 0.49.0 / 22.0.0 |
| Database | PostgreSQL (Supabase) via asyncpg | 0.31.0 |
| ORM | SQLAlchemy 2.0 (async) | 2.0.51 |
| Migrations | Alembic | 1.18.5 |
| Authentication | JWT (python-jose) | 3.5.0 |
| AI Provider SDK | Groq Python SDK | 1.5.0 |
| AI API Client | httpx (Pollinations, NVIDIA) | 0.28.1 |
| Screenshots | Playwright + Cloudinary | 1.60.0 / 1.44.2 |
| Lead Discovery | SerpAPI (via httpx) | — |
| Frontend | React 19 / TypeScript 6 / Vite 8 | — |
| State | Zustand 5 / TanStack Query 5 | — |
| Styling | Tailwind CSS 4 + CVA + clsx | — |
| Charts | Recharts | 3.9.0 |
| Icons | Lucide React | 1.21.0 |

---

## 4. Current Repository Structure

```
D:\Leadforge AI/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── api/v1/endpoints/        # Route handlers (thin)
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── leads.py
│   │   ├── analysis.py
│   │   ├── screenshots.py
│   │   ├── audits.py
│   │   ├── outreach.py
│   │   ├── generation.py
│   │   ├── dashboard_endpoint.py
│   │   └── settings.py
│   ├── core/                    # Config, exceptions, logging, security
│   ├── database/                # Session, Base
│   ├── dependencies/            # Auth dependency
│   ├── middleware/              # Error handler, request ID
│   ├── models/                  # SQLAlchemy models (9)
│   ├── repositories/            # CRUD layer (9)
│   ├── schemas/                 # Pydantic schemas (13)
│   └── services/                # Business logic
│       ├── ai/                  # Architecture A: Groq + Pollinations + NVIDIA
│       ├── audit_engine.py
│       ├── auth.py
│       ├── cloudinary_service.py
│       ├── dashboard_service.py
│       ├── discovery.py
│       ├── lead.py
│       ├── lead_scoring.py
│       ├── markdown_engine/     # Full content generation pipeline
│       ├── outreach.py
│       ├── screenshot.py
│       ├── serpapi.py
│       ├── settings.py
│       ├── website_analyzer.py
│       ├── website_blueprint/   # DEAD — unused alternative blueprint system
│       ├── website_generator/   # Generation pipeline with 2 sub-architectures
│       │   ├── static_html_generator.py  # CANONICAL — the production generator
│       │   ├── generator.py               # DEAD — unused old WebsiteGenerator
│       │   ├── blueprint.py               # DEAD — unused old BlueprintBuilder
│       │   ├── blueprint_schemas.py       # DEAD — unused old blueprint schemas
│       │   ├── context_builder.py
│       │   ├── prompt_builder.py
│       │   ├── providers/       # Architecture B: Groq + Pollinations + NVIDIA
│       │   ├── response_parser.py         # RE-EXPORT wrapper (keep)
│       │   ├── parsers/response_parser.py # CANONICAL response parser
│       │   ├── renderers/                 # DEAD — unused renderer subsystem
│       │   ├── templates/                 # DEAD — unused template subsystem
│       │   ├── build/           # Build pipeline (used by deployments)
│       │   ├── deployment/      # Package manager, manifest (USED)
│       │   └── preview/         # Preview engine (USED)
│       └── website_intelligence/  # Playwright crawl, profile builder
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # React Router + QueryClient + Zustand
│   │   ├── main.tsx
│   │   ├── layouts/             # DashboardLayout, Sidebar, TopBar, etc.
│   │   ├── pages/               # 14 pages
│   │   ├── components/          # Reusable UI components
│   │   ├── services/            # apiClient.ts + services.ts
│   │   ├── store/               # Zustand stores (auth, project, ui)
│   │   ├── types/               # TypeScript types
│   │   ├── hooks/               # Custom hooks
│   │   ├── contexts/            # Theme + Error contexts
│   │   └── utils/               # Utility functions
│   ├── vercel.json              # SPA rewrites
│   └── vite.config.ts
├── alembic/                     # 8 linear migrations, single head
├── Dockerfile
├── requirements.txt
└── tests/
    └── test_provider_fallback.py  # 25 tests for provider chain
```

---

## 5. Canonical Backend Modules

| Responsibility | Canonical File | Route | Status |
|---|---|---|---|
| App entrypoint | `app/main.py` | — | Working |
| Health | `app/api/v1/endpoints/health.py` | `GET /health` | Working |
| Auth | `app/services/auth.py` | `POST /api/v1/auth/*` | Working |
| Lead CRUD | `app/services/lead.py` | `GET/POST/PATCH /api/v1/leads/*` | Working |
| Screenshot | `app/services/screenshot.py` | `POST /api/v1/screenshots/*` | Working |
| Website Analysis | `app/services/website_analyzer.py` | `POST /api/v1/analysis/*` | Working |
| AI Audit | `app/services/audit_engine.py` | `POST /api/v1/audits/run` | Working (needs API key) |
| AI Providers (Arch A) | `app/services/ai/{groq,pollinations,nvidia}.py` | — | Working |
| Lead Scoring | `app/services/lead_scoring.py` | — | Working |
| Website Gen | `app/services/website_generator/static_html_generator.py` | `POST /api/v1/generation/generate` | Working |
| Context Builder | `app/services/website_generator/context_builder.py` | — | Working |
| Prompt Builder | `app/services/website_generator/prompt_builder.py` | — | Working |
| Providers (Arch B) | `app/services/website_generator/providers/` | — | Working |
| Response Parser | `app/services/website_generator/parsers/response_parser.py` | — | Working |
| Markdown Engine | `app/services/markdown_engine/builder.py` | — | Working |
| Website Intelligence | `app/services/website_intelligence/service.py` | — | Working |
| Build Engine | `app/services/website_generator/build/` | — | Working |
| Package Manager | `app/services/website_generator/deployment/package_manager.py` | — | Working |
| Preview Engine | `app/services/website_generator/preview/` | — | Working |
| Outreach | `app/services/outreach.py` | `POST /api/v1/outreach/generate` | Working |
| Dashboard | `app/services/dashboard_service.py` | `GET /api/v1/dashboard/*` | Working |
| Settings | `app/services/settings.py` | `GET/PUT /api/v1/settings/*` | Working |
| Lead Discovery | `app/services/discovery.py` | `POST /api/v1/leads/discover` | Working |
| SerpAPI | `app/services/serpapi.py` | — | Working |

---

## 6. Canonical Frontend Modules

| Page | Route | File | Status |
|---|---|---|---|
| Login | `/login` | `LoginPage.tsx` | Working |
| Register | `/register` | `RegisterPage.tsx` | Working |
| Dashboard | `/dashboard` | `DashboardPage.tsx` | Working |
| Projects (leads) | `/projects` | `ProjectsPage.tsx` | Working |
| Lead Detail | `/project/:id` | `LeadDetailPage.tsx` | Working |
| Generation | `/generation` | `GenerationPage.tsx` | Working |
| Preview | `/preview/:websiteId` | `PreviewPage.tsx` | Working |
| Deployment | `/deployment/:websiteId` | `DeploymentPage.tsx` | Working |
| History | `/history` | `HistoryPage.tsx` | Working |
| Analytics | `/analytics` | `AnalyticsPage.tsx` | Working |
| Settings | `/settings` | `SettingsPage.tsx` | Working |
| Help | `/help` | `HelpPage.tsx` | Working |
| 404 | `*` | `NotFoundPage.tsx` | Working |
| Layout | — | `DashboardLayout.tsx` | Working |
| Sidebar | — | `Sidebar.tsx` | Working |
| TopBar | — | `TopBar.tsx` | Working |
| Activity Panel | — | `RightActivityPanel.tsx` | Working |
| Status Bar | — | `FooterStatusBar.tsx` | Working |

---

## 7. Database Models and Migrations

### Models (9 total)

| Model | Table | Key Relationships |
|---|---|---|
| `User` | `users` | Has many leads |
| `Lead` | `leads` | Belongs to user, has one audit/screenshot/score/outreach/many generated_websites |
| `Audit` | `audits` | Belongs to lead |
| `Screenshot` | `screenshots` | Belongs to lead |
| `LeadScore` | `lead_scores` | Belongs to lead |
| `Outreach` | `outreaches` | Belongs to lead |
| `GeneratedWebsite` | `generated_websites` | Belongs to lead |
| `RevokedToken` | `revoked_tokens` | — |
| `UserSettings` | `user_settings` | Belongs to user |

### Migrations

- **Head**: `f8a1b2c3d4e5` (add generated websites)
- **Chain**: 8 linear migrations, no branches
- **Status**: Single head, no conflicts, no duplicate IDs

---

## 8. Actual API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/auth/register` | Register user |
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT |
| `POST` | `/api/v1/auth/logout` | Logout |
| `GET` | `/api/v1/auth/me` | Current user |
| `GET` | `/api/v1/leads` | List leads (paginated) |
| `POST` | `/api/v1/leads` | Create lead |
| `POST` | `/api/v1/leads/discover` | Discover leads via SerpAPI |
| `GET` | `/api/v1/leads/{id}` | Lead detail |
| `PATCH` | `/api/v1/leads/{id}` | Update lead |
| `DELETE` | `/api/v1/leads/{id}` | Delete lead |
| `GET` | `/api/v1/leads/export/csv` | CSV export |
| `POST` | `/api/v1/analysis/analyze` | Website analysis |
| `GET` | `/api/v1/analysis/{lead_id}` | Get analysis |
| `POST` | `/api/v1/screenshots/capture` | Capture screenshots |
| `GET` | `/api/v1/screenshots/{lead_id}` | Get screenshots |
| `POST` | `/api/v1/audits/run` | AI audit + scoring |
| `POST` | `/api/v1/outreach/generate` | Generate outreach |
| `POST` | `/api/v1/generation/build` | Build website intelligence |
| `POST` | `/api/v1/generation/generate` | Generate website |
| `GET` | `/api/v1/generation/websites/{id}` | Get generated website |
| `GET` | `/api/v1/generation/leads/{id}/latest` | Get latest generated |
| `GET` | `/api/v1/generation/websites/{id}/download` | Download ZIP |
| `GET` | `/api/v1/dashboard/summary` | Dashboard summary |
| `GET` | `/api/v1/dashboard/recent-leads` | Recent leads |
| `GET` | `/api/v1/dashboard/status-distribution` | Status distribution |
| `GET` | `/api/v1/settings/profile` | Get profile |
| `PUT` | `/api/v1/settings/profile` | Update profile |
| `GET` | `/api/v1/settings/preferences` | Get preferences |
| `PUT` | `/api/v1/settings/preferences` | Update preferences |
| `GET` | `/api/v1/settings/account-summary` | Account summary |

---

## 9. AI Provider Architecture

### Architecture A (Audit + Outreach)
```
AIBaseProvider (ABC, dict-based)
├── GroqProvider      — groq SDK (primary)
├── PollinationsProvider — httpx → text.pollinations.ai (secondary)
└── NvidiaProvider    — httpx → integrate.api.nvidia.com (tertiary)

AIFactory: fallback chain = ["groq", "pollinations", "nvidia"]
Called by: AuditEngineService, OutreachService
```

### Architecture B (Website Generation)
```
AIProvider (ABC, AIResponse-based)
├── GroqProvider      — httpx → api.groq.com (primary)
├── PollinationsProvider — httpx → text.pollinations.ai (secondary)
└── NvidiaProvider    — httpx → integrate.api.nvidia.com (tertiary)

ProviderFactory: fallback chain = ["groq", "pollinations", "nvidia"]
Called by: StaticHTMLGenerator
```

### Provider Configuration

| Variable | Required | Default |
|---|---|---|
| `GROQ_API_KEY` | No (but primary) | — |
| `GROQ_DEFAULT_MODEL` | No | `llama-3.3-70b-versatile` |
| `GROQ_BASE_URL` | No | `https://api.groq.com` |
| `POLLINATIONS_API_KEY` | No (open mode) | — |
| `POLLINATIONS_BASE_URL` | No | `https://text.pollinations.ai` |
| `NVIDIA_API_KEY` | No (but tertiary) | — |
| `NVIDIA_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_AUDIT_MODEL` | No | `meta/llama-3.1-8b-instruct` |
| `NVIDIA_GENERATION_MODEL` | No | `meta/llama-3.1-8b-instruct` |

---

## 10. What Is Fully Working

- Health check
- User registration, login, JWT refresh, logout
- Lead CRUD (create, list, detail, update, delete)
- Lead CSV export
- Website analysis (scraper)
- Screenshot capture (Playwright → Cloudinary)
- AI Audit → Lead Score pipeline (if provider configured)
- Website generation → preview persistence → ZIP download
- Generated website detail, latest-by-lead query
- Outreach generation (if audit data exists)
- Dashboard summary, recent leads, status distribution
- Settings (profile, preferences, account summary)
- All frontend pages render, navigate, and display data
- Frontend auth state (Zustand + JWT + silent refresh)
- API client (axios with token interceptor + refresh queue)
- All 25 provider fallback tests pass

---

## 11. What Is Partially Working

- **AI Audit/Outreach**: 503 when no provider API key is configured in the deployment environment. The fallback chain correctly tries all 3 providers but all fail without credentials.
- **Vercel SPA routing**: `vercel.json` committed but Vercel auto-deploy not triggering — SPA rewrites not active in production.
- **Website intelligence build**: Works but the 216KB `service.py` is monolithic and contains a third unused blueprint generator.

---

## 12. What Is Broken

- **AI Audit in production**: HTTP 503 — requires at least one of `GROQ_API_KEY`, `POLLINATIONS_API_KEY`, or `NVIDIA_API_KEY` to be set in Railway. Currently none are configured (only `GEMINI_API_KEY` which is no longer used).
- **Frontend preview on Vercel**: Sub-routes (`/preview/{id}`) return 404 because `vercel.json` with SPA rewrites was committed but never deployed (Vercel auto-deploy not triggering from GitHub).

---

## 13. What Is Unverified

- Pollinations AI provider in production (works without API key but untested under load)
- NVIDIA NIM provider in production (requires API key to verify)
- Frontend build on Railway/Vercel after latest changes
- `POLLINATIONS_AUDIT_MODEL` — Pollinations model auto-discovery is untested

---

## 14. What Was Duplicated

Two competing **blueprint systems** — both dead in production:
1. `website_generator/blueprint.py` + `blueprint_schemas.py` — older, simpler (330 lines)
2. `website_blueprint/` — newer, more elaborate (entire package, ~2000 lines)
3. `website_intelligence/service.py` `generate_website_blueprint()` method — a third variant embedded in the service (unused)

Two competing **generators** — one dead, one canonical:
1. `website_generator/generator.py` `WebsiteGenerator` — unused (138 lines)
2. `website_generator/static_html_generator.py` `StaticHTMLGenerator` — production (199 lines)

**Dead renderer subsystem** (superseded by StaticHTMLGenerator):
- `website_generator/renderers/` — entire package (NextJSRenderer, FileGenerator, TemplateRegistry)
- `website_generator/templates/` — entire package (TemplateEngine, 10 section templates)

**Orphaned package**:
- `app/routers/` — empty, not imported

**Frontend dead code**:
- `useProjectStore` (store/projectStore.ts) — never imported
- `useDeploymentStore` (store/uiStores.ts) — never imported
- `deploymentsService` (services/services.ts) — never imported
- `refreshTokens` function (services/services.ts) — never imported
- `Size`, `Tone`, `WebsiteAnalysisRequest` types (types/index.ts) — never imported

**Debug scripts (tracked, not harmful)**:
- `tmp_e2e_integration.py`, `tmp_test_providers.py`, `test_auth_bug.py`, `test_final_e2e.py`, `test_full_e2e.py`, `debug_reg.py`, `debug_reg2.py`, `prep_tests.py`, `clean_db.py`, `_clean.py`

---

## 15. What Was Removed (this audit)

- Empty `__pycache__/` directories (all)
- `.pytest_cache/`
- `logs/` (1MB `app.log`) — ignored by `.gitignore`
- `.agents/` — empty agent working directory
- `frontend/src/app/`, `frontend/src/assets/`, `frontend/src/lib/`, `frontend/src/styles/` — empty orphan dirs

### Cleanup NOT done (preserved for safety)
- All dead code tracked in git (blueprint systems, renderers, WebsiteGenerator, etc.)
- Debug scripts (tracked source files)
- Unused frontend stores, types, services (tracked source files)
- `app/routers/` (tracked source file, though only `__init__.py`)

---

## 16. What Was Kept and Why

| File | Reason Kept |
|---|---|
| `website_generator/blueprint.py` | Tracked; not imported in production but referenced by debug scripts |
| `website_blueprint/` package | Tracked; could be useful reference if blueprint system is revived |
| `website_generator/generator.py` | Tracked; referenced by debug scripts |
| `website_generator/renderers/` | Tracked; substantial codebase, could inform future renderer |
| `website_generator/templates/` | Tracked; section templates used by renderers |
| `app/routers/` | Tracked; only `__init__.py` exists — harmless |
| Debug scripts (10 files) | Tracked; useful for future debugging even if not part of test suite |
| `useProjectStore`, `useDeploymentStore` | Tracked; harmless, no consumers to break |
| `deploymentsService`, `refreshTokens` | Tracked; no consumers to break |
| `unused types` | Tracked; tiny, harmless |

---

## 17. Deployment Configuration

### Railway
- **Backend URL**: `https://leadforge-ai-production-eff1.up.railway.app`
- **Dockerfile**: `Dockerfile` (Python 3.12-slim, Playwright + Chromium)
- **Start command**: `gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 1 --timeout 300`
- **Auto-deploy**: GitHub `main` branch
- **Status**: Health 200, migrations auto-run on startup

### Vercel
- **Frontend URL**: `https://lead-forge-ai-tan.vercel.app`
- **Root directory**: `frontend/`
- **Build command**: `npm run build`
- **Output directory**: `dist/`
- **SPA routing**: `vercel.json` committed (rewrites to `/index.html`)
- **Status**: Auto-deploy not triggering; SPA routes not active

---

## 18. Required Environment Variable Names

```
ENV, DEBUG, PORT, HOST, LOG_LEVEL
CORS_ORIGINS
JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
DATABASE_URL
SCREENSHOTS_DIR
SERPAPI_KEY
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
GROQ_API_KEY, GROQ_DEFAULT_MODEL, GROQ_BASE_URL
POLLINATIONS_API_KEY, POLLINATIONS_AUDIT_MODEL, POLLINATIONS_GENERATION_MODEL, POLLINATIONS_BASE_URL
NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_AUDIT_MODEL, NVIDIA_GENERATION_MODEL
FRONTEND_URL
```

---

## 19. Known Production URLs

- Backend: `https://leadforge-ai-production-eff1.up.railway.app`
- Frontend: `https://lead-forge-ai-tan.vercel.app`
- API Docs: `https://leadforge-ai-production-eff1.up.railway.app/docs`

---

## 20. Current Test Status

| Test Suite | Result | Notes |
|---|---|---|
| `tests/test_provider_fallback.py` | 25/25 PASS | Provider factory, fallback chain, error handling |
| `comprehensive_test.py` (live) | 18/19 PASS | AI Audit fails (no provider API key in Railway) |
| Frontend `tsc --noEmit` | PASS | No TypeScript errors |
| Backend `import app.main` | PASS | All imports resolve |

---

## 21. Current Deployment Status

| Service | Status | URL | Notes |
|---|---|---|---|
| Railway (backend) | ✅ Healthy (200) | `leadforge-ai-production-eff1.up.railway.app` | Latest commit `f46dd57` deployed |
| Vercel (frontend) | ⚠️ Live but stale | `lead-forge-ai-tan.vercel.app` | Vercel auto-deploy not triggering |
| Database (Supabase) | ✅ Connected | `qptloaobjyzvgyyiebvg` | Migrations run on Railway startup |

---

## 22. Remaining Blockers

1. **No provider API key in Railway** → Set `GROQ_API_KEY` (or any fallback) in Railway env
2. **Vercel auto-deploy not triggering** → May need Vercel CLI redeploy or GitHub integration re-link
3. **Pollinations model discovery** → Untested in production; may need explicit `POLLINATIONS_GENERATION_MODEL` set
4. **`GROQ_BASE_URL` in `.env.example`** has `/openai/v1` suffix while code default does not — inconsistent
5. **`GEMINI_API_KEY`** still in Railway env but unused — safe, but unnecessary

---

## 23. Exact Recommended Implementation Order

1. **Configure Railway env**: Set `GROQ_API_KEY` (highest priority), `NVIDIA_API_KEY` (backup), remove unused `GEMINI_API_KEY`
2. **Force Vercel redeploy**: Either reconnect GitHub integration or use Vercel CLI `npx vercel --prod`
3. **Clean up dead code** (next non-audit sprint):
   - Delete: `website_generator/generator.py`, `website_generator/blueprint.py`, `website_generator/blueprint_schemas.py`, `website_generator/renderers/`, `website_generator/templates/`, `website_blueprint/`, `app/routers/`
   - Delete frontend dead code: `projectStore.ts`, unused types, `deploymentsService`, `refreshTokens`
   - Delete tracked debug scripts (`tmp_*`, `test_*_bug.py`, etc.)
4. **Fix `GROQ_BASE_URL` inconsistency** in `.env.example` (remove `/openai/v1` suffix)
5. **Consider refactoring `website_intelligence/service.py`** from 216KB monolith into smaller modules
6. **Verify end-to-end workflow** in production with configured provider

---

## 24. Files That Must Not Be Replaced

- `app/main.py` — app entrypoint, all routes registered here
- `app/core/config.py` — all env vars, single source of truth
- `app/core/exceptions.py` — consistent app exception hierarchy
- `app/database/session.py` — async engine + session factory
- `app/database/base.py` — declarative base with auto-tablename
- `app/middleware/error_handler.py` — exception → JSON response mapping
- `app/dependencies/auth.py` — JWT auth dependency
- `app/services/audit_engine.py` — audit orchestrator with fallback chain
- `app/services/outreach.py` — outreach orchestrator with fallback chain
- `app/services/website_generator/static_html_generator.py` — production generator
- `app/services/website_generator/parsers/response_parser.py` — canonical response parser
- `app/services/website_generator/providers/base.py` — provider ABC
- `app/services/website_generator/providers/provider_factory.py` — registry + fallback
- `app/services/ai/base.py` — AIBaseProvider ABC
- `app/services/ai/factory.py` — registry + fallback
- `app/repositories/base.py` — base CRUD
- All 9 SQLAlchemy model files
- All 9 repository files
- All 13 schema files
- All Alembic migration files
- `Dockerfile`, `requirements.txt`, `frontend/vercel.json`

---

## 25. Rules for Future Coding Agents

1. **There are TWO AI provider architectures**: Architecture A (`app/services/ai/`) for audit/outreach (dict-based, `AIBaseProvider` ABC) and Architecture B (`app/services/website_generator/providers/`) for generation (`AIResponse`-based, `AIProvider` ABC). Both have fallback chains. Do not create a third.
2. **Fallback chain order**: Groq → Pollinations → NVIDIA → safe failure. Fallback only for rate limit, timeout, connection error, temporary provider failure. Not for invalid input or missing prerequisites.
3. **Production generator**: `StaticHTMLGenerator` is the only generator used in production. `WebsiteGenerator`, `BlueprintBuilder`, `WebsiteBlueprintBuilder`, `NextJSRenderer` are all dead code.
4. **Frontend API base URL**: Controlled by `VITE_API_BASE_URL` env var. The `apiClient.ts` normalizes it to ensure `/api/v1` suffix. Do not hardcode URLs.
5. **Frontend auth**: Zustand `useAuthStore` for state, `apiClient.ts` interceptor for silent JWT refresh. Do not create a second auth system.
6. **Database models**: 9 models, each with corresponding repository and schema. Do not create duplicate models/repos/schemas.
7. **Alembic migrations**: Linear chain, single head. Always create new migrations for schema changes, never edit existing ones.
8. **Provider credentials**: Never hardcode API keys. All keys come from environment variables via `app/core/config.py`.
9. **Frontend navigation**: Only navigate to preview when `website_id` is present. `unwrap()` in services.ts already throws on `success=false`.
10. **Do not deploy**: Only commit to `main` when explicitly asked. Push audit branches separately.

---

## 26. Earlier Frontend Versions and Recoverable Features

### Git History of Frontend

| Commit | Description | Impact |
|---|---|---|
| `9d61396` | Initial commit | First frontend skeleton |
| `428d40c` | Initial production-ready commit | Working MVP with all pages |
| `f7f1148` | Set frontend API URL to Railway | Configuration change |
| `8d82eac` | CORS and API URL configuration | Configuration change |
| `21ab039` | Add /api/v1 to API base URL | Configuration change |
| `526487a` | Normalize VITE_API_BASE_URL | Configuration change |
| `32a48bf` | Various fixes | Multi-domain fix |
| `9174bb2` | Update FRONTEND_URL to Vercel URL | Configuration change |
| `177b7e4` | **Restore audit result, detect existing website** | Major feature addition |
| `342261a` | Add vercel.json for SPA routing | Deployment config |
| `f46dd57` | Add AI provider fallback chain | Current HEAD |

### Feature Comparison

| Feature / UI Element | Earlier (428d40c) | Current (f46dd57) | Functional? | Recommendation |
|---|---|---|---|---|
| Lead Detail — existing website detection | Not present | Present (177b7e4) | ✅ Functional | Keep current |
| Lead Detail — audit reconstruction from lead data | Not present | Present (177b7e4) | ✅ Functional | Keep current |
| Lead Detail — workflow-status-aware buttons | Not present | Present (177b7e4) | ✅ Functional | Keep current |
| Lead Detail — `website_id` guard | Not present | Present (f46dd57) | ✅ Functional | Keep current |
| Lead Detail — overall structure | Simpler | Enriched | ✅ All features additive | Keep current |
| Projects page | Present | Present | ✅ Functional | Keep current |
| Generation page | Present | Present | ✅ Functional | Keep current |
| Preview page | Present | Present | ✅ Functional | Keep current |
| Deployment page | Present | Present | ✅ Functional | Keep current |
| Dashboard page | Present | Present | ✅ Functional | Keep current |
| Settings page | Present | Present | ✅ Functional | Keep current |
| Analytics page | Present | Present | ✅ Functional | Keep current |
| History page | Present | Present | ✅ Functional | Keep current |
| Help page | Present | Present | ✅ Functional | Keep current |

### Key Finding

**No frontend features were lost.** Between the initial production commit (428d40c) and the current HEAD (f46dd57), the frontend has only been modified with:

1. Configuration changes (API URLs, CORS)
2. The `177b7e4` feature enrichment (existing website detection, audit reconstruction, workflow-status buttons)
3. The `f46dd57` navigation guard

All 14 pages exist in both versions with incremental improvements. No UI elements, layouts, stores, or service methods were removed at any point.

If the user recalls an earlier version with preferred UI elements, that version is `428d40c` (the initial production-ready commit). However, all features from that version are still present in the current codebase — any perceived differences would be styling/design choices that evolved naturally, not features that were lost.
