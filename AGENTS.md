# LeadForge AI — Session Summary

## Goal
Fix all failing features (screenshot, AI audit, website generation, lead creation, lead detail) in the Railway production deployment and make the entire app 100% functional.

## Constraints & Preferences
- Backend: `https://leadforge-ai-production-eff1.up.railway.app`
- Frontend: `https://lead-forge-oyjnslyea-ahsansagheer071-8737s-projects.vercel.app`
- Branch: `ui/antigravity-premium-theme` (active development)
- Database: Supabase PostgreSQL (`qptloaobjyzvgyyiebvg`)
- All code pushed to GitHub `main` auto-deploys to Railway
- No direct Railway/Vercel console access; debugging via HTTP response analysis
- Windows local dev environment with Python 3.14 and PowerShell

## Progress

### All 19 Endpoints Passing (comprehensive_test.py)
```
1.  Health check ─────────────────────── 200
2.  User Registration ────────────────── 201
3.  Login (form-encoded) ─────────────── 200
4.  Create Lead ──────────────────────── 201
5.  Website Analysis ─────────────────── 200
6.  AI Audit ─────────────────────────── 200/503*  (*Groq free tier)
7.  Screenshot ───────────────────────── 200
8.  Generate Website ─────────────────── 200
9.  List Leads ───────────────────────── 200
10. Generate Outreach ────────────────── 200/422*  (*requires audit data)
11. Lead Detail ──────────────────────── 200
12. Dashboard (3 endpoints) ──────────── 200
13. Settings (3 endpoints) ───────────── 200
14. PATCH Lead ───────────────────────── 200
15. CSV Export ───────────────────────── 200
```

### What Was Fixed

| Issue | Root Cause | Fix |
|---|---|---|
| **Screenshot 503** | `--single-process` crash, missing libs, concurrent retry race | Removed flag, added deps, sequential capture |
| **Lead Detail 500** | `weaknesses` schema `List[WeaknessItem]` → AI returns `List[str]` | Changed to `List[str]` |
| **Website Gen 404** | `build_profile()` never called (dead code) | Auto-build on `/generate`, new `/build` endpoint |
| **Website Gen 500** | `ColorPalette.frequency: None`, missing `heading_font`, missing `ctas`/`title`/`era`/`traits` aliases | Schema fixes + alias fields |
| **Website Gen 500** | `re.search(args, re.IGNORECASE)` — flags swapped with string | Fixed arg order |
| **Website Gen IntegrityError** | `save_profile()` called twice (in `build_profile` + endpoint) | Removed duplicate call, upsert in `save_profile` |
| **Groq OOM** | `build_profile` launched separate browser alongside BrowserManager | Reused BrowserManager singleton |
| **Groq 429/timeout** | Multiple strategies × retries exhausted free tier limits | Reduced to 1 strategy, 2 attempts, 65s rate limit backoff |
| **Groq `e` scoping** | `str(e)` in `else` block where `e` undefined on TimeoutError | `last_error` pattern |
| **Screenshot oversize** (new) | 18 MB desktop PNG exceeds Cloudinary 10 MB limit | Added `_optimize_image()` via Pillow: resize to 1920px, WebP, progressive quality reduction until < 9.5 MB |
| **getStageState error priority** (new) | `getStageState` checks mutation error BEFORE persisted data, so a failed recapture overwrites valid previous result | `rawState()` now checks: active → hasData → error → pending; `getStageState()` uses first-non-completed-index logic |
| **Generation error messages** (new) | Generic "Could not reach the backend" for all generation failures | Categorized messages for network, timeout, provider, and auth errors in both LeadDetailPage and GenerationPage |

## Known Issues
1. **Groq free tier**: AI Audit/Outreach may fail under load (30 RPM / 30k TPM limit). Upgrade to paid plan for reliability.
2. **No Gemini fallback**: Configured but untested.
3. **Generation network error** (Issue 2, ongoing diagnosis): Consistent `!ax.response` (category `network`) when Vercel frontend calls Railway `/generation/generate`. Not a timeout (not ECONNABORTED). Likely Railway infrastructure proxy timeout during cold start + long Playwright/AI chain. Fallback: improved error messages + 300s explicit per-request timeout.

## Relevant Files
- `app/services/screenshot.py` — BrowserManager singleton, `_optimize_image()`
- `app/schemas/audit.py` — `weaknesses: List[str]`
- `app/services/website_intelligence/service.py` — `build_profile()`, schema fixes
- `app/services/website_intelligence/schemas.py` — Typography, HeroInfo, DesignLanguageResult
- `app/api/v1/endpoints/generation.py` — `/build`, `/generate` endpoints
- `app/services/ai/groq.py` — Rate limit handling, 1 strategy
- `app/services/audit_engine.py` — 300s timeout
- `app/services/website_generator/static_html_generator.py` — Fixed regex args
- `frontend/src/pages/LeadDetailPage.tsx` — `rawState()`/`getStageState()`/`getActiveStage()`; generation & screenshot error handlers
- `frontend/src/pages/GenerationPage.tsx` — generation error handler
- `frontend/src/services/apiClient.ts` — `extractApiError`, `getApiErrorMessage`
- `comprehensive_test.py` — 19-endpoint test suite
