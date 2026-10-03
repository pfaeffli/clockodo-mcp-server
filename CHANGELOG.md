# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Sick days** (#30): New `add_my_sick_day(date_since, date_until, sick_note=False, child=False)` tool (absence type 4, or 5 for a sick day of a child). `create_team_member_vacation` accepts `sick_note` and sends `False` for types 4 and 5 when omitted, as Clockodo requires the field there.

### Fixed
- **API error details** (#30): Clockodo's JSON error body is now included in the raised error message (`... - Details: ...`); previously it was swallowed and only the bare HTTP error was shown.

## [0.6.0] - 2026-10-03

### Added
- **Half-day vacations** (#39, #42, #44): `add_my_vacation` takes `half_day=True` for a single-day half-day absence (Clockodo rejects multi-day half days, so the tool does too before calling the API). New `edit_my_vacation(absence_id, date_since, date_until, half_day)` changes the dates or half-day flag of your own absence, e.g. to turn a 4-day vacation into 3.5 days: shorten it to the full days and add the half day separately. It refuses absences that belong to other users, even with a team-leader API key.

### Changed
- **SBOM release upload** (#41): A separate `attach-sbom` job with only `contents: write` uploads the per-arch SBOMs to the GitHub release; `build-and-scan` stays read-only. Publish the release right after pushing the tag, or re-run `attach-sbom` afterwards.

## [0.5.0] - 2026-10-02

### Added
- **Self-Service Absence Listing** (#25, #27): New `get_my_absences(year, absence_type=None)` tool lists the authenticated user's absences for a year across all statuses (enquired, approved, declined, cancelled). Each entry includes the `id` required by `delete_my_vacation` / `adjust_vacation_dates`, plus `date_since`, `date_until`, `type`, `status` and `count_days`. Filtering by user and type happens server-side via `filter[users_id]` / `filter[type]`.
- **Claude Code GitHub workflows** (#32): Automatic Claude code review on same-repo PRs (skipped for forks, superseded runs cancelled) and `@claude` mentions in issues and PRs.

### Fixed
- **HR Overtime Double-Count** (#24): `get_hr_summary` / `check_overtime_compliance` no longer add the prior-year overtime carryover on top of `diff`. Clockodo's `diff` already includes the carryover, so the previous behaviour inflated balances and produced false-positive `excessive_overtime` violations. `overtime_hours` now equals `diff / 3600`.
- **Absence type docs**: Docstrings for `add_absence` / team-leader absence tools now match Clockodo's codes (2 = special leave, 3 = overtime reduction, 4 = sick day); type 2 was previously documented as "Illness".

### Security
- **Dependabot alerts cleared** (#28, #31): Runtime floors `anyio>=4.14.2` (critical TLS host-name spoofing) and `idna>=3.15`; dev dependencies bumped (black, wheel, pytest, python-dotenv, pygments).
- **Trivy waivers** (#29, #31): Unfixable Debian base-image CVEs triaged in `.trivyignore` with expiry dates and reachability notes; expired waivers refreshed; `pip` dropped from the runtime image.
- **CI determinism**: Pinned `mcp<2` and `ruff` to match the lockfile.

## [0.4.1] - 2026-05-10

See the [v0.4.1 release notes](https://github.com/pfaeffli/clockodo-mcp-server/releases/tag/v0.4.1).

## [0.4.0] - 2026-02-15

See the [v0.4.0 release notes](https://github.com/pfaeffli/clockodo-mcp-server/releases/tag/v0.4.0).

## [0.3.2] - 2026-02-10

See the [v0.3.2 release notes](https://github.com/pfaeffli/clockodo-mcp-server/releases/tag/v0.3.2).

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
