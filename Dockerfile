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

# Optional override for builds without a usable repository (e.g. worktrees)
ARG SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CLOCKODO_MCP

# Copy project files including the repository metadata for version discovery
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

# Remove pip from the runtime image: nothing needs it at runtime, and the
# base image's pip vendors setuptools 70.3.0 (CVE-2025-47273) and
# msgpack 1.1.2 (GHSA-6v7p-g79w-8964), both flagged HIGH by the gating
# Trivy scan with no in-place fix short of dropping pip.
RUN python -m pip uninstall -y pip

# Default env vars for Clockodo (override at runtime)
ENV CLOCKODO_BASE_URL="https://my.clockodo.com/api/"

USER appuser

# No HEALTHCHECK: the default transport is stdio, so there is no endpoint to
# probe, and spawning a second process only proves the entry point imports.
# Run SSE behind an orchestrator probe on the published port if needed.
#
# SSE example (binds all interfaces inside the container, so a bearer token is
# mandatory; publish the port on loopback only):
#   docker run -p 127.0.0.1:8000:8000 \
#     -e CLOCKODO_MCP_TRANSPORT=sse -e CLOCKODO_MCP_HOST=0.0.0.0 \
#     -e CLOCKODO_MCP_AUTH_TOKEN=... -e CLOCKODO_MCP_ALLOWED_HOSTS='localhost:*,127.0.0.1:*' \
#     clockodo-mcp

# Default command starts the MCP server entrypoint
ENTRYPOINT ["clockodo-mcp"]
