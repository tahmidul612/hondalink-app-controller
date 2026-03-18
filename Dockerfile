# Multi-stage build for minimal image size
# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
# Use --no-dev to skip development dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen --no-dev

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Install runtime dependencies only
# - adb for Android debugging
# - ca-certificates for HTTPS
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        adb \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash hondalink && \
    mkdir -p /app/logs && \
    chown -R hondalink:hondalink /app

# Copy virtual environment from builder
COPY --from=builder --chown=hondalink:hondalink /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=hondalink:hondalink src/ ./src/
COPY --chown=hondalink:hondalink README.md ./

# Switch to non-root user
USER hondalink

# Add virtual environment to PATH
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run with uvicorn
# Use single worker for resource efficiency
# Stateful Android connection requires single-process mode
CMD ["uvicorn", "src.hondalink.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info", \
     "--no-access-log"]
