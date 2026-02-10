# syntax=docker/dockerfile:1
# Stage 1: Builder
# This stage installs git and uses it to discover the version via setuptools-scm.
# It installs the package into a temporary directory.
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install git for setuptools-scm versioning
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files including .git for version discovery
COPY . .

# Install project into a prefix directory
RUN pip install --upgrade pip && \
    pip install --prefix=/install .

# Stage 2: Final
# This stage is the deliverable. It contains only the installed package
# and its runtime dependencies. No git, no .git directory.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime system dependencies and apply security patches
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser
WORKDIR /app

# Copy the installed files from the builder stage
COPY --from=builder /install /usr/local

# Default env vars for Clockodo (override at runtime)
ENV CLOCKODO_BASE_URL="https://my.clockodo.com/api/v2/"

USER appuser

# Health check for MCP server
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD clockodo-mcp --help > /dev/null || exit 1

# Default command starts the MCP server entrypoint
ENTRYPOINT ["clockodo-mcp"]
