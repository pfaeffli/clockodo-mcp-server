# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-01-14

### Added
- **Automated Versioning**: Implemented `setuptools-scm` to synchronize project version with Git tags automatically.
- **Dynamic Version Discovery**: Updated package to retrieve version information at runtime using `importlib.metadata`.

### Fixed
- **Development Environment**: Fixed `Dockerfile.dev` build failure by providing a fallback version for `setuptools-scm` during the build phase.
- **Code Quality**: Excluded auto-generated `_version.py` from Black, isort, Ruff, and Pylint to prevent pipeline failures.
- **CI/CD Pipeline**: Fixed persistent permission errors in the linting pipeline by disabling Ruff's cache (`--no-cache`) and redirecting other tool caches to `/tmp`. Removed unsupported `--no-cache` flag from `isort`.

### Security
- **Multi-stage Docker Build**: Optimized Docker image by using a multi-stage build, excluding build-time dependencies like `git` and the `.git` directory from the final deliverable.

## [0.3.0] - 2026-01-14
(This version was used for testing automated tagging)

## [0.2.0] - 2026-01-14

### Added
- **Project Discovery**: Added `list_projects` tool to discover Clockodo projects.
- **Project Resource**: Added `clockodo://projects` resource for LLM context.
- **Enhanced Tools**: Support for `projects_id` in `start_my_clock` and `add_my_time_entry`.
- **API Version Documentation**: New section in `README.md` explaining version handling strategy.

### Changed
- **API Modernization**: Upgraded all endpoints to latest stable versions:
    - **v4**: Projects, Services, Absences.
    - **v3**: Users, Customers.
    - **v2**: Clock, Time Entries.
- **Robust Client**: Implemented `__post_init__` URL normalization to handle malformed `CLOCKODO_BASE_URL` (e.g., stripping `/v2/` suffixes).
- **Response Normalization**: Unified data structures by mapping generic `data` keys to plural resource keys (e.g., `users`, `projects`).
- **Improved User Service**: Enhanced `get_current_user_id` to reliably identify authenticated users across different API response patterns.
- **Manual Testing**: Expanded Jupyter notebook with comprehensive end-to-end workflows.

### Fixed
- **404 Route Not Found**: Resolved issues where incorrect base URLs led to invalid API paths (e.g., `.../api/v2/v3/users`).
- **Inconsistent Responses**: Fixed parsing errors for v3/v4 endpoints that returned data under a generic `data` key instead of plural keys.
- **User Discovery**: Fixed failure to identify the authenticated user when the email address matched but the response structure was unexpected.

### Security
- **Pipeline Verification**: Verified with full suite of security scans (Trivy, Dockle, License check).
