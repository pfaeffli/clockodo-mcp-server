# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN useradd -m appuser
WORKDIR /app

# System deps (if needed later). Keep minimal for fast builds.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for better caching
COPY pyproject.toml /app/
COPY src /app/src

# Install project (runtime deps only)
RUN pip install --upgrade pip && \
    pip install .

# Default env vars for Clockodo (override at runtime)
ENV CLOCKODO_BASE_URL="https://my.clockodo.com/api/v2/"

USER appuser

# Default command starts the MCP server entrypoint
ENTRYPOINT ["clockodo-mcp"]
