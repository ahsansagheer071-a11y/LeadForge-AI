# ===================================================
# Stage 1 — Build dependencies
# ===================================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ===================================================
# Stage 2 — Runtime production image
# ===================================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PATH="/root/.local/bin:$PATH"

# Runtime deps: PostgreSQL client, curl (healthcheck), Playwright OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxcb1 libxkbcommon0 libxdamage1 \
    libxcomposite1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

# Install Playwright + Chromium only (smallest browser)
RUN pip install --no-cache-dir playwright && \
    playwright install chromium && \
    rm -rf /root/.cache && \
    rm -rf /var/lib/apt/lists/*

# Copy application code (only what's needed at runtime)
COPY requirements.txt alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/

# Create screenshot directory
RUN mkdir -p app/static/screenshots

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-"]
