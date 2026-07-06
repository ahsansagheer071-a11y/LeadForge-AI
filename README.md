# LeadForge AI Backend

LeadForge AI is a production-ready, highly scalable AI-powered Lead Intelligence SaaS backend designed for digital marketing agencies. It streamlines B2B lead generation, automating lead discovery, deep website auditing, screenshot capture, automated AI outreach drafting, and scoring.

---

## Features

- **JWT Authentication & Security**: Complete secure authorization with role-based restrictions.
- **Lead Discovery**: Integrated with SerpAPI Google Maps search with automated duplicate prevention.
- **Website Analyzer**: Hompage crawler extracting metadata, visual structure elements, email, and phone contact points.
- **Screenshot Service**: Playwright Chromium integrations producing desktop, mobile, and full-page captures.
- **AI Audit Engine**: LLM auditing of business setups and sites to draft detailed marketing feedback.
- **Outreach Generator**: Contextual email templates, call-to-actions, and LinkedIn scripts powered by LLM.
- **Dashboard Analytics**: Fast aggregated reporting for user-specific pipeline tracking.
- **Robust Settings management**: User profile settings, change-password constraints, and UI preferences.
- **Docker-Compose Ready**: Complete containerization out-of-the-box.

---

## Folder Structure

```text
├── alembic/                # Database migrations config and scripts
├── app/
│   ├── api/                # FastAPI Endpoints & Routers
│   ├── core/               # App configuration, security, exceptions, and logging
│   ├── database/           # Engine and async sessionmakers
│   ├── dependencies/       # Authentication filters
│   ├── middleware/         # Request ID logging and error handling
│   ├── models/             # SQLAlchemy ORM Models
│   ├── repositories/       # Generic Base and specialized repos
│   ├── schemas/            # Pydantic validation schemas
│   ├── services/           # Orchestrated business logic services
│   └── main.py             # Entrypoint & startup/shutdown logic
├── .dockerignore           # Ignored files for Docker builds
├── .env.example            # Environment variables template
├── docker-compose.yml      # Docker Multi-container orchestration
├── Dockerfile              # Docker multi-stage build file
├── requirements.txt        # Pinned python packages
└── README.md               # Product documentation
```

---

## Running Locally

### Prerequisites

- Python 3.12+
- PostgreSQL
- Node.js (for Playwright installation testing if desired)

### Setup

1. **Clone and Navigate**:
   ```bash
   cd Leadforge-AI
   ```

2. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   playwright install-deps chromium
   ```

4. **Environment File**:
   Copy `.env.example` to `.env` and configure your database URI and API keys:
   ```bash
   cp .env.example .env
   ```

5. **Apply Migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **Interactive Docs**:
   Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) to access Swagger.

---

## Docker Deployment

Deploying with Docker is the recommended route for production environments.

1. **Build & Start Containers**:
   ```bash
   docker-compose up -d --build
   ```

2. **Verify Startup**:
   Check container logs to verify database connectivity, startup validation checks, and API availability:
   ```bash
   docker-compose logs -f web
   ```

3. **Stop Environment**:
   ```bash
   docker-compose down -v
   ```

---

## Environment Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENV` | Environment context (`development`, `production`) | `production` |
| `DEBUG` | Enable debug logs and tracebacks | `false` |
| `CORS_ORIGINS` | Allowed origins separated by comma | `http://localhost:3000` |
| `JWT_SECRET` | Signing secret for OAuth tokens | `super-secret-hex-key` |
| `DATABASE_URL` | PostgreSQL Async connection string | `postgresql://user:pass@db:5432/leadforge_ai` |
| `SERPAPI_KEY` | Key for Lead discovery engine | (Optional per-user) |
| `GROQ_API_KEY` | Key for AI audits & Outreach generation | (Optional per-user) |
