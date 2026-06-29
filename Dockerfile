# ==========================================
# Stage 1: Build Dependencies
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install compiler tools for any python binary extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install dependencies into a wheels directory
RUN pip install --no-cache-dir --user -r requirements.txt


# ==========================================
# Stage 2: Runtime Production Environment
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies for PostgreSQL client and Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Install Playwright browsers and system dependencies
# We only need chromium for desktop screenshot captures to keep image size small
RUN pip install --no-cache-dir playwright && \
    playwright install chromium && \
    playwright install-deps chromium && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY . .

# Expose port
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
