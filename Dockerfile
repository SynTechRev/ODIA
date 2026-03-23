# =============================================================================
# Stage 1 — Backend builder
# Install Python dependencies into a venv for clean copying
# =============================================================================
FROM python:3.11-slim AS backend-builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the packaging files first (layer-cache friendly)
COPY pyproject.toml ./
COPY src/ ./src/

# Create venv and install
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install --no-cache-dir .

# =============================================================================
# Stage 2 — Frontend builder
# Build Next.js standalone output
# =============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend

# Install dependencies first (layer-cache friendly)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# Copy source and build
COPY frontend/ ./

# NEXT_PUBLIC_API_URL is baked at build time — nginx proxies /api/* on port 8080
ENV NEXT_PUBLIC_API_URL=http://localhost:8080

RUN npm run build

# =============================================================================
# Stage 3 — Production image
# Combines Python venv, Next.js standalone, nginx, supervisord
# =============================================================================
FROM python:3.11-slim AS production

WORKDIR /app

# Install nginx, supervisord, curl (for health check), and Node.js runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Node.js binary from builder (same Debian base — compatible)
COPY --from=frontend-builder /usr/local/bin/node /usr/local/bin/node

# Copy Python venv
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY templates/ ./templates/
COPY legal/ ./legal/
COPY schemas/ ./schemas/
COPY scripts/ ./scripts/

# Copy Next.js standalone build
COPY --from=frontend-builder /build/frontend/.next/standalone ./frontend/standalone
COPY --from=frontend-builder /build/frontend/.next/static ./frontend/standalone/.next/static
COPY --from=frontend-builder /build/frontend/public ./frontend/standalone/public

# Install nginx and supervisord config
COPY scripts/docker-nginx.conf /etc/nginx/sites-available/odia
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/odia /etc/nginx/sites-enabled/odia
COPY scripts/docker-supervisord.conf /etc/supervisord.conf

# Install entrypoint
COPY scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Runtime directories
RUN mkdir -p /data/documents /data/reports /app/reports /app/manifests

# Environment
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED="1"

# API keys — override at runtime via -e or docker-compose environment
ENV OPENAI_API_KEY=""
ENV ANTHROPIC_API_KEY=""

# Persistent user data (documents, reports)
VOLUME ["/data"]

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
