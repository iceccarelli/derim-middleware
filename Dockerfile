# =============================================================================
# DERIM Middleware – Production Docker Image
# =============================================================================
# Multi-stage build for a lean, secure container.
#
# Build:
#   docker build -t derim-middleware:latest .
#
# Run:
#   docker run -p 8000:8000 derim-middleware:latest
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time system dependencies.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching.
COPY requirements/ requirements/
RUN pip install --no-cache-dir --prefix=/install \
    -r requirements/base.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="DERIM Project <derim@example.com>"
LABEL description="Smart Grid Digital Twin Middleware for DER Integration"
LABEL version="0.1.0"

# Create a non-root user for security.
RUN groupadd --gid 1000 derim && \
    useradd --uid 1000 --gid derim --shell /bin/bash --create-home derim

# Copy installed Python packages from builder.
COPY --from=builder /install /usr/local

# Set working directory.
WORKDIR /app

# Copy application source code.
COPY src/ src/
COPY pyproject.toml .
COPY requirements/ requirements/

# Create data and model directories.
RUN mkdir -p /app/data /app/saved_models /app/logs && \
    chown -R derim:derim /app

# Install the package in editable mode (for proper imports).
RUN pip install --no-cache-dir -e .

# Switch to non-root user.
USER derim

# Expose the API port.
EXPOSE 8000

# Health check.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default environment variables.
ENV DERIM_APP_NAME="derim-middleware" \
    DERIM_APP_ENV="production" \
    DERIM_LOG_LEVEL="INFO" \
    DERIM_STORAGE_BACKEND="sqlite" \
    DERIM_SQLITE_DB_PATH="/app/data/derim.db" \
    DERIM_MODEL_SAVE_DIR="/app/saved_models"

# Run the FastAPI application with Uvicorn.
CMD ["uvicorn", "derim.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
