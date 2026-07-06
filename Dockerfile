FROM python:3.12-slim AS runner

WORKDIR /app

ENV \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PATH="/root/.local/bin:$PATH" \
  PLAYWRIGHT_BROWSERS_PATH=/root/playwright-browsers

# Install ALL system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    libpq5 \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxcb1 libxkbcommon0 libxdamage1 \
    libxcomposite1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 \
    libxcursor1 libxfixes3 libgtk-3-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps + Playwright + Chromium
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "playwright==1.60.0" && \
    playwright install --with-deps chromium && \
    rm -rf /root/.cache

# Copy application code (only what's needed at runtime)
COPY requirements.txt alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/

# Create screenshot directory
RUN mkdir -p app/static/screenshots

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "300", "--access-logfile", "-"]
