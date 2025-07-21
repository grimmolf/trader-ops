# Multi-stage Dockerfile for TraderTerminal Web + Backend
# Stage 1: Build frontend assets
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files for dependency installation
COPY package*.json ./
COPY apps/web/package*.json ./apps/web/
COPY packages/ui/package*.json ./packages/ui/

# Install dependencies
RUN npm ci

# Copy source files
COPY apps/web ./apps/web
COPY packages/ui ./packages/ui

# Build shared UI package first
RUN npm run build --workspace=packages/ui

# Build web app
RUN npm run build --workspace=apps/web

# Stage 2: Python backend with static files
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --user-group --uid 1000 trader

# Copy Python requirements and source
COPY pyproject.toml uv.lock ./
COPY src/backend ./src/backend

# Install Python dependencies using uv for speed
RUN pip install uv && \
    uv pip install --system -e .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/apps/web/dist ./static/web

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R trader:trader /app

# Switch to non-root user
USER trader

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONPATH=/app
ENV STATIC_FILES_ENABLED=true
ENV STATIC_FILES_DIRECTORY=static/web
ENV HOST=0.0.0.0
ENV PORT=8000

# Start server
CMD ["python", "-m", "uvicorn", "src.backend.datahub.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]