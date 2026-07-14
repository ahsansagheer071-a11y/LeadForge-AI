# LeadForge AI — Project Guide

## Architecture

### Stack
- **Backend**: FastAPI (Python 3.14), deployed on Railway
- **Frontend**: React + TypeScript + Vite, deployed on Vercel
- **Database**: Supabase PostgreSQL (Alembic migrations)
- **AI Providers**: Groq (primary), Nvidia, Pollinations (for audit/outreach only via `app/services/ai/`)

### Backend Endpoints
```
POST /api/v1/auth/register     — User registration
POST /api/v1/auth/login        — Login (form-encoded)
GET  /api/v1/dashboard/stats   — Dashboard aggregate stats
GET  /api/v1/dashboard/recent  — Recent activity
GET  /api/v1/dashboard/charts  — Chart data
GET  /api/v1/leads              — List leads
POST /api/v1/leads              — Create lead
GET  /api/v1/leads/{id}         — Lead detail
PATCH /api/v1/leads/{id}        — Update lead
DELETE /api/v1/leads/{id}       — Delete lead
GET  /api/v1/leads/export/csv   — CSV export
POST /api/v1/website/analyze    — Website analysis (URL → profile)
POST /api/v1/website/screenshot — Screenshot capture
POST /api/v1/website/build      — Build WebsiteProfile from URL
POST /api/v1/audit/generate     — AI audit (uses app/services/ai/)
POST /api/v1/outreach/generate  — AI outreach (uses app/services/ai/)
POST /api/v1/generation/build   — Build WebsiteProfile
POST /api/v1/generation/generate — Generate website (sync, uses DesignProvider)
POST /api/v1/generation/jobs    — Generate website (async, uses DesignProvider)
GET  /api/v1/generation/jobs/{id} — Job status
POST /api/v1/generation/jobs/{id}/cancel — Cancel job
GET  /api/v1/preview/{id}       — Preview HTML
POST /api/v1/deploy             — Deploy / package
GET  /api/v1/settings/profile   — User profile
PUT  /api/v1/settings/profile   — Update profile
PUT  /api/v1/settings/password  — Change password
GET  /api/v1/settings/preferences — Preferences
PUT  /api/v1/settings/preferences — Update preferences
GET  /health                    — Health check
```

### Key Modules

#### `app/services/ai/` — AI Audit & Outreach (PRESERVED)
- `groq.py`, `nvidia.py`, `pollinations.py` — Provider implementations for audit/outreach chain
- `chain.py` — `AIChain` orchestrator with provider fallback
- `base.py` — `BaseAIProvider` ABC
- This directory is **not** related to the website visual design pipeline

#### `app/services/website_generator/` — Visual Design Pipeline
- `design_provider.py` — `DesignProvider` ABC + `DesignProviderNotConfigured` stub
- `schemas.py` — `GenerationResult`, `WebsiteProject`, `GeneratedFile`
- `prompt_budget.py` — `PromptBudgetController` (used by future DesignProvider implementations)
- `fidelity_validator.py` — `FidelityValidator` (used by future DesignProvider implementations)
- `asset_packager.py` — `AssetPackager` for ZIP packaging
- `build/schemas.py` — `BuildResult`, `ValidationReport` (local imports from generation.py)
- `preview/schemas.py` — `PreviewResult`, `InstanceInfo` (local imports from generation.py)
- `parsers/schemas.py` — `GeneratedAsset`, `ProjectMetadata`, `ProjectStatistics` (used by PackageManager)
- `deployment/package_manager.py` — ZIP packaging for future Stitch integration

#### `app/services/markdown_engine/` — Content Extraction
- `builder.py` — `MarkdownBuilder` assembles `MarkdownPackage` (rules, profile, screenshots, assets)
- `source_content.py` — Extracts content markdown from WebsiteProfile
- `schemas.py` — `MarkdownPackage` with `asset_manifest: Optional[AssetManifest]`
- This module feeds data to the DesignProvider but is independent of it

#### `app/services/website_intelligence/` — Website Analysis
- `service.py` — `WebsiteIntelligenceService` (crawl, analyze, build profile)
- `schemas.py` — `WebsiteProfile`, `Typography`, `HeroInfo`, `DesignLanguageResult`
- `_reconstruct_from_flat_db()` on WebsiteProfile for DB → Pydantic hydration

#### `app/services/screenshot.py` — BrowserManager singleton

#### `app/models/` — SQLAlchemy models
- `generation_job.py` — `GenerationJob` with `provider_used` column
- `lead.py`, `user.py`, `project.py` — core domain models

#### `app/schemas/audit.py` — `weaknesses: List[str]`

### Frontend
- `src/pages/GenerationPage.tsx` — Pre-flight shows "upgrading" notice when DesignProvider not configured
- `src/services/services.ts` — API client (no `generateWebsite`, no `deploymentsService`)
- `src/store/uiStores.ts` — Only `usePreviewStore` (no `useProjectStore`, `useDeploymentStore`, `useNotificationsStore`)
- `src/types/index.ts` — No `GenerateWebsiteResponse`
- Theme: dark-only, no toggle

### Preserved for Future Stitch Integration
- `PromptBudgetController` — Caps prompt tokens for free-tier LLMs
- `FidelityValidator` — Validates generated HTML against source website
- `AssetPackager` — Packages generated site into ZIP
- `PackageManager` — Handles asset bundling
- All schema files (`build/schemas.py`, `preview/schemas.py`, `parsers/schemas.py`)

## Constraints
- No direct Railway/Vercel console access; debugging via HTTP response analysis
- Windows local dev environment with Python 3.14 and PowerShell
- Groq must NOT be removed from AI Audit or Outreach (uses `app/services/ai/`)
- Google Stitch: Phase 1 = manual import POC (no Python SDK exists, TypeScript SDK only)

## Stitch Integration (Phase 1 — Manual Import POC)

### Architecture
- `app/services/website_generator/stitch/brief.py` — `BriefGenerator` builds `PremiumRedesignBrief` from lead data
- `app/services/website_generator/stitch/import_provider.py` — `StitchImportProvider` imports Stitch HTML exports
- `app/services/website_generator/stitch/schemas.py` — Stitch-specific schemas

### Workflow
1. `POST /stitch/brief` → generates `PremiumRedesignBrief` with full instruction text
2. User copies brief into Google Stitch → Stitch generates design
3. User exports HTML from Stitch
4. `POST /stitch/import` → imports HTML, validates, stores, previews, packages

### Stitch MCP Availability
- **MCP available**: yes (remote endpoint at `stitch.googleapis.com/mcp`)
- **TypeScript SDK**: `@google/stitch-sdk` v0.3.5
- **Python SDK**: none (Phase 2 would need Node.js sidecar or direct MCP calls)
- **Authentication**: `STITCH_API_KEY` env var or OAuth
- **Export format**: HTML/CSS (self-contained), React/JSX, Vue, Tailwind
- **Manual import required**: yes (Phase 1)

## Testing
- `python -m pytest tests/` — Backend tests (230 pass, 9 network-dependent kissthehippo tests expected to fail without internet)
- `npx tsc --noEmit` — TypeScript check (0 errors)
- `npm run lint` — Lint (0 warnings)
- `npm run build` — Vite production build

## Git Workflow
- `main` branch auto-deploys to Railway (backend) and Vercel (frontend)
- Feature branches for cleanup/refactor work
- Commit messages: conventional style (`refactor:`, `fix:`, `feat:`)
