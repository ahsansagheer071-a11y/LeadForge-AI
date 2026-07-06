# LeadForge AI — Deployment Guide

## Prerequisites

- Node.js 24+
- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (optional)

---

## 1. Environment Variables

### Backend (`./.env`)

Copy `.env.example` to `.env` and fill all values:

| Variable | Required | Description |
|----------|----------|-------------|
| `ENV` | Yes | `production` |
| `DEBUG` | Yes | `false` |
| `PORT` | Yes | `8000` |
| `CORS_ORIGINS` | Yes | Comma-separated frontend URL(s) |
| `JWT_SECRET` | Yes | `openssl rand -hex 32` |
| `DATABASE_URL` | Yes | `postgresql://user:pass@host:5432/leadforge_ai` |
| `SERPAPI_KEY` | Yes | SerpAPI key for lead discovery |
| `GROQ_API_KEY` | Yes | Groq key for AI inference |
| `CLOUDINARY_CLOUD_NAME` | Yes | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Yes | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Yes | Cloudinary API secret |

### Frontend (`./frontend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Backend origin (e.g. `https://api.your-domain.com`) |

> `VITE_API_BASE_URL` is embedded at **build time**. You must rebuild if it changes.

---

## 2. Database — Run Migrations

```bash
# Ensure .env has DATABASE_URL pointing to your PostgreSQL instance
alembic upgrade head
```

To verify current state:
```bash
alembic current
```

Migration chain (7 migrations, linear):
```
27407898bb22 (initial)
  → a3f8b2c91d04 (website analyzer columns)
  → b4e9c3d02e15 (screenshot table)
  → c5f8e4d01b23 (explanation in lead_scores)
  → d6f9e5d02c34 (outreach fields)
  → 447b08563f58 (settings + profile fields)
  → e7f0a4b12c56 (markdown_package_metadata)
```

---

## 3. Backend Deployment

### Option A: Docker (recommended for VPS / Railway / Render)

```bash
# Build
docker build -t leadforge-api -f Dockerfile .

# Run (with PostgreSQL)
docker run -d \
  --name leadforge_api \
  -p 8000:8000 \
  --env-file .env \
  leadforge-api
```

Startup command: `gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --timeout 120`

### Option B: Docker Compose (full stack)

```bash
docker compose up -d
```

This starts PostgreSQL + the API with auto-restart and health checks.

### Option C: Railway

1. Connect GitHub repo
2. Set root as `./`
3. Build command: (none — Railway uses Dockerfile)
4. Start command: `gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4 --timeout 120`
5. Add environment variables from `.env.example`
6. Add a PostgreSQL plugin (Railway provides `DATABASE_URL`)

### Option D: Render (Web Service)

1. Create a "Web Service" from your GitHub repo
2. Runtime: Docker
3. Health check path: `/health`
4. Add environment variables from `.env.example`
5. Add a PostgreSQL database (Render provides `DATABASE_URL`)

### Option E: VPS (Ubuntu + Docker)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone and deploy
git clone https://github.com/your-org/leadforge-ai.git
cd leadforge-ai
cp .env.example .env
nano .env  # fill secrets

# Run with Docker Compose
docker compose up -d

# Or as a standalone container
docker build -t leadforge-api .
docker run -d --restart always -p 8000:8000 --env-file .env leadforge-api

# Run migrations
docker exec leadforge_web alembic upgrade head
```

**Reverse proxy (Nginx)**:
```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Then get SSL via Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.your-domain.com
```

---

## 4. Frontend Deployment

### Option A: Vercel (recommended)

1. Connect your GitHub repo
2. Set root directory: `frontend`
3. Framework preset: **Vite**
4. Build command: `npm run build`
5. Output directory: `dist`
6. Environment variable:
   - `VITE_API_BASE_URL` = `https://api.your-domain.com`
7. Deploy

### Option B: Netlify

1. Connect your GitHub repo
2. Base directory: `frontend`
3. Build command: `npm run build`
4. Publish directory: `frontend/dist`
5. Environment variable:
   - `VITE_API_BASE_URL` = `https://api.your-domain.com`
6. Add `/* /index.html 200` redirect rule for SPA fallback
7. Deploy

### Option C: Docker (Nginx)

```bash
# Build with API URL
docker build -t leadforge-web --build-arg VITE_API_BASE_URL=https://api.your-domain.com -f frontend/Dockerfile frontend/

docker run -d --restart always -p 80:80 leadforge-web
```

---

## 5. Security Checklist

- [ ] `JWT_SECRET` is a 64-char hex string (`openssl rand -hex 32`)
- [ ] `DEBUG=false` in production
- [ ] `CORS_ORIGINS` is set to the exact frontend domain (not `*`)
- [ ] `DATABASE_URL` uses a strong password
- [ ] All Cloudinary/SERPAPI/Groq keys are valid
- [ ] Frontend is served over HTTPS
- [ ] Backend is behind a reverse proxy with HTTPS termination
- [ ] Playwright Chromium is installed (for screenshot capture)
- [ ] Database connection pool limits: pool_size=20, max_overflow=10

---

## 6. Post-Deployment Verification

```bash
# 1. Health check
curl https://api.your-domain.com/health

# Expected response:
# { "status": "online", "database": "healthy", "services": { ... } }

# 2. API docs
# Open https://api.your-domain.com/docs

# 3. Frontend
# Open https://app.your-domain.com

# 4. Test auth
# Register a user & log in

# 5. Test lead discovery
# Create a lead via the UI

# 6. Test AI features
# Website analysis, audit, screenshot, outreach, generation
```

---

## 7. Monitoring & Logs

- Backend logs: `logs/app.log` (rotating, 10 MB × 5 files)
- Docker logs: `docker logs leadforge_web`
- Each request is logged with a unique `X-Request-ID`

---

## 8. Scaling Considerations

- **Database**: Neon PostgreSQL is recommended for serverless auto-scaling
- **Workers**: Gunicorn with 4 workers (`--workers 4`) — adjust based on CPU cores
- **Playwright**: Single-instance only; do not run multiple API containers with Playwright without coordinating screenshot captures
- **Session pooling**: 20 pool connections with 10 overflow — sufficient for 4 gunicorn workers
