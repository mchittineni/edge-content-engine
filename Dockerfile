# ==============================================================================
# Stage 1: Build virtual environment and wheels
# ==============================================================================
FROM python:3.14-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# The source must be present before building the wheel. Copying only
# pyproject.toml produced a wheel containing no packages, so the runtime image
# installed an empty distribution and `edge --help` failed with
# ModuleNotFoundError: No module named 'cli'.
COPY pyproject.toml README.md ./
COPY packages/ ./packages/
COPY agents/ ./agents/
COPY apps/ ./apps/
COPY cli/ ./cli/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels .

# ==============================================================================
# Stage 2: Minimal hardened runtime
# ==============================================================================
FROM python:3.14-slim AS runtime

# Security hardening: Run as non-root user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies from builder
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Application code arrives via the installed wheel above, so only non-package
# data and metadata are copied here.
COPY --chown=appuser:appgroup prompts/ ./prompts/
COPY --chown=appuser:appgroup pyproject.toml README.md ./

# Create content directory structure with correct permissions
RUN mkdir -p content/drafts content/diagrams content/research content/state content/published content/raw content/analytics && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
