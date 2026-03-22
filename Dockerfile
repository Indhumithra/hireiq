# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps for building Python packages (spacy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Download spacy model (en_core_web_sm) — small, ~12 MB
RUN python -m spacy download en_core_web_sm || true

# Create directories used at runtime
RUN mkdir -p uploads

# Environment defaults (can be overridden at runtime)
ENV FLASK_ENV=production \
    PORT=5000

EXPOSE 5000

# Use gunicorn for production
CMD ["python", "run.py"]
