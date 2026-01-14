# Clockodo MCP Server

MCP server wrapper for the Clockodo time tracking API with configurable feature sets.

[![MCP Badge](https://lobehub.com/badge/mcp/pfaeffli-clockodo-mcp-server)](https://lobehub.com/mcp/pfaeffli-clockodo-mcp-server)
[![Docker Image](https://ghcr-badge.egpl.dev/pfaeffli/clockodo-mcp-server/latest_tag?trim=major&label=latest)](https://github.com/pfaeffli/clockodo-mcp-server/pkgs/container/clockodo-mcp-server)
[![Security Scans](https://img.shields.io/badge/security-scanned-green)](https://github.com/pfaeffli/clockodo-mcp-server/actions)

**🐳 Docker Image:** `ghcr.io/pfaeffli/clockodo-mcp-server:latest`

## Table of Contents
- [Features](#features)
- [Architecture & Patterns](#architecture--patterns)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Available Features](#available-features)
- [Development](#development)
- [Manual Testing](#manual-testing)

## Features

This MCP server provides comprehensive time tracking capabilities through:

- **Tools**: 25+ tools for time tracking, HR analytics, and team management
- **Prompts**: Interactive prompt templates for common workflows
- **Resources**: Real-time access to time entries, customers, and services
- **Role-Based Access**: Configurable permission levels (employee, team_leader, hr_analytics, admin)

## Architecture & Patterns

This project follows specific architectural patterns to maintain clean, testable, and maintainable code.

### 1. **Layered Architecture**

```
┌─────────────────────────────────────┐
│   MCP Server Layer (server.py)     │  ← Tool registration, MCP protocol
├─────────────────────────────────────┤
│   Service Layer (services/)         │  ← Business logic, orchestration
├─────────────────────────────────────┤
│   Client Layer (client.py)          │  ← HTTP API communication
├─────────────────────────────────────┤
│   External API (Clockodo REST API)  │  ← Third-party service
└─────────────────────────────────────┘
```

**Rules:**
- **Server Layer**: Only handles MCP tool registration and protocol. No business logic.
- **Service Layer**: Contains all business logic. Services use clients but never handle MCP directly.
- **Client Layer**: Pure HTTP/API client. No business logic, only request/response handling.
- **Dependencies flow downward only**: Server → Service → Client (never upward)

### 2. **Configuration Management**

**Pattern**: Feature Flags with Environment Variables

```python
# config.py - Central configuration
class ServerConfig:
    hr_readonly: bool = True      # Default safe
    user_read: bool = False        # Opt-in
    admin_edit: bool = False       # Explicit opt-in

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load from environment with safe defaults"""
```

**Rules:**
- All configuration comes from environment variables
- Safe defaults (read-only, minimal permissions)
- Preset configurations available (readonly, user, admin)
- No hardcoded credentials or API keys

### 3. **Dependency Injection**

**Pattern**: Constructor Injection

```python
class HRService:
    def __init__(self, client: ClockodoClient):
        """Inject dependencies explicitly"""
        self.client = client

    def check_overtime_compliance(self, year: int) -> dict:
        # Use injected client
        reports = self.client.get_user_reports(year=year)
```

**Rules:**
- Services receive their dependencies through constructors
- Makes testing easy (mock the dependencies)
- Clear dependency graph
- No global state or singletons (except config)

### 4. **Separation of Concerns**

**Pattern**: Single Responsibility Principle

```
client.py          → HTTP communication only
hr_analyzer.py     → Pure data analysis (no I/O)
hr_service.py      → Orchestration (client + analyzer)
hr_tools.py        → MCP tool wrappers (service → MCP)
server.py          → Tool registration
```

**Rules:**
- Each module has ONE clear purpose
- Analyzers are pure functions (input → output, no side effects)
- Services handle orchestration
- Tools are thin wrappers

### 5. **API Version Handling**

**Pattern**: Resource-Specific Versioning

Clockodo uses a resource-specific versioning scheme. This server always targets the most recent stable version for each resource:
- **v4**: Projects, Services, Absences
- **v3**: Users, Customers
- **v2**: Clock, Entries
- **v1**: User Reports (Legacy reports with no newer version available)

**Rules:**
- Base URL is normalized to end with `/api/`
- All client methods explicitly use the required version prefix (e.g., `v3/users`)
- Responses are normalized to maintain internal consistency (e.g., mapping `data` key to resource-specific keys)
- Legacy v1 endpoints are called without a version prefix

### 6. **Error Handling**

**Pattern**: Let Errors Bubble Up with Context

```python
def _request(self, method: str, endpoint: str) -> dict:
    resp = httpx.request(...)
    resp.raise_for_status()  # Let HTTPStatusError bubble up
    return resp.json()
```

**Rules:**
- Don't catch exceptions unless you can handle them
- Use httpx's built-in error handling
- Add context when re-raising
- Let MCP framework handle final error presentation

### 7. **Type Safety**

**Pattern**: Type Hints Everywhere

```python
def check_overtime_compliance(
    self, year: int, max_overtime_hours: float = 80
) -> dict:
    """
    Clear input/output types

    Args:
        year: Year to check (e.g., 2024)
        max_overtime_hours: Maximum allowed overtime hours

    Returns:
        Dictionary with overtime violations
    """
```

**Rules:**
- All functions have type hints
- Use `from __future__ import annotations` for forward references
- Docstrings explain the structure of complex dicts
- mypy validation in CI/CD

### 8. **Testing Strategy**

**Pattern**: Layered Testing

```
Unit Tests          → Pure functions (analyzers)
Integration Tests   → Services with mocked clients
Manual Tests        → Jupyter notebooks for real API
```

**Rules:**
- Mock external HTTP calls (use respx)
- Test business logic in isolation
- Use pytest fixtures for common setup
- Manual testing with real credentials in notebooks

### 9. **Documentation as Code**

**Pattern**: Self-Documenting Code

```python
@mcp.tool()
def check_overtime_compliance(year: int, max_overtime_hours: float = 80) -> dict:
    """
    Check which employees have excessive overtime.

    This docstring becomes the MCP tool description.
    """
```

**Rules:**
- Docstrings on all public functions
- Type hints provide inline documentation
- README explains patterns and architecture
- Examples in manual-test/ folder

### 10. **Environment-Based Behavior**

**Pattern**: Configuration Over Code

```python
# Don't do this:
if production_mode:
    do_something()

# Do this:
config = ServerConfig.from_env()
if config.is_enabled(FeatureGroup.ADMIN_EDIT):
    register_admin_tools()
```

**Rules:**
- Feature flags control behavior
- No if/else for environments in code
- Test different configurations via env vars
- Document all environment variables

---

## Setup

### Option 1: Using Pre-built Docker Image from GitHub Container Registry

#### For Local MCP Clients (Claude Desktop, IDEs) - stdio transport

Add configuration to your IDE's MCP settings (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "clockodo": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "CLOCKODO_API_USER=your@email.com",
        "-e",
        "CLOCKODO_API_KEY=your_api_key",
        "-e",
        "CLOCKODO_USER_AGENT=my-company/1.0",
        "-e",
        "CLOCKODO_BASE_URL=https://my.clockodo.com/api/v2/",
        "-e",
        "CLOCKODO_EXTERNAL_APP_CONTACT=dev@company.com",
        "-e",
        "CLOCKODO_MCP_ROLE=employee",
        "ghcr.io/pfaeffli/clockodo-mcp-server:latest"
      ]
    }
  }
}
```

#### For Remote Access (Web Apps) - HTTP/SSE transport

> **⚠️ Note:** SSE transport is currently experimental and has known issues. Not recommended for production use.

```bash
docker run -d \
  -p 8000:8000 \
  -e CLOCKODO_API_USER=your@email.com \
  -e CLOCKODO_API_KEY=your_api_key \
  -e CLOCKODO_MCP_ROLE=employee \
  -e CLOCKODO_MCP_TRANSPORT=sse \
  -e CLOCKODO_MCP_HOST=0.0.0.0 \
  -e CLOCKODO_MCP_PORT=8000 \
  ghcr.io/pfaeffli/clockodo-mcp-server:latest
```

**Available image tags:**
- `latest` - Latest stable release
- `v1.0.0`, `v1.0`, `v1` - Semantic version tags
- `main-<sha>` - Latest main branch build

### Option 2: Build Locally

1. Build the Docker image:
   ```bash
   make build-mcp
   ```

2. Add configuration to your IDE's MCP settings using `clockodo-mcp:latest` instead of the ghcr.io image.

## Environment Variables

### API Credentials (Required)
- `CLOCKODO_API_USER` - Your Clockodo email
- `CLOCKODO_API_KEY` - Your Clockodo API key

### API Configuration (Optional)
- `CLOCKODO_USER_AGENT` - Custom user agent string (default: "clockodo-mcp/unknown")
- `CLOCKODO_BASE_URL` - API base URL (default: "https://my.clockodo.com/api/v2/")
- `CLOCKODO_EXTERNAL_APP_CONTACT` - Contact info for external app header (default: API user email)

### Transport Configuration (Optional)
- `CLOCKODO_MCP_TRANSPORT` - Transport protocol (default: "stdio")
  - `stdio` - Standard input/output for local processes (Claude Desktop, IDEs) **[Recommended]**
  - `sse` - HTTP/SSE for remote access **[Experimental - Known Issues]**
- `CLOCKODO_MCP_HOST` - Host address to bind to (default: "0.0.0.0")
- `CLOCKODO_MCP_PORT` - Port for SSE transport (default: 8000)

> **⚠️ SSE Transport Limitation:** The SSE transport is experimental and currently has issues with the MCP library (v1.25.0). The server accepts connections and messages but does not properly send responses back through the event stream, causing client initialization timeouts. **Use stdio transport for production.** SSE support depends on upstream fixes in the MCP library.

### Role Configuration (Recommended)

Use `CLOCKODO_MCP_ROLE` to set the user's role:

```bash
CLOCKODO_MCP_ROLE=employee      # Default - Track your own time
CLOCKODO_MCP_ROLE=team_leader   # Employee + approve vacations & edit team entries
CLOCKODO_MCP_ROLE=hr_analytics  # View HR compliance reports only
CLOCKODO_MCP_ROLE=admin         # Full access to everything
```

| Role | Can Do |
|------|--------|
| **employee** | Track own time, request vacation |
| **team_leader** | Everything employee can + approve team vacations + edit team entries |
| **hr_analytics** | View HR compliance reports (overtime, vacation violations) for all employees |
| **admin** | Full access to all features |

### Legacy Configuration (Deprecated)

The following are still supported but deprecated. Use `CLOCKODO_MCP_ROLE` instead:

**Legacy Presets:**
- `CLOCKODO_MCP_PRESET=readonly` - Maps to hr_analytics role
- `CLOCKODO_MCP_PRESET=user` - Maps to employee role
- `CLOCKODO_MCP_PRESET=team_leader` - Maps to team_leader role
- `CLOCKODO_MCP_PRESET=admin` - Maps to admin role

**Legacy Granular Flags:**
- `CLOCKODO_MCP_ENABLE_HR_READONLY=true`
- `CLOCKODO_MCP_ENABLE_USER_READ=true`
- `CLOCKODO_MCP_ENABLE_USER_EDIT=true`
- `CLOCKODO_MCP_ENABLE_TEAM_LEADER=true`
- `CLOCKODO_MCP_ENABLE_ADMIN_READ=true`
- `CLOCKODO_MCP_ENABLE_ADMIN_EDIT=true`

## Available Features

### Core Tools (Always Available)
- `health` - Health check (shows enabled features)
- `list_users` - List all Clockodo users
- `list_customers` - List all customers
- `list_services` - List all services
- `list_projects` - List all projects
- `get_raw_user_reports(year)` - Get raw API response for debugging

### Prompts (Always Available)
- `start_tracking` - Start tracking time for a customer and service
- `stop_tracking` - Stop tracking the current time entry
- `request_vacation` - Request vacation time

### Resources (Always Available)
- `clockodo://current-entry` - Get the currently running time entry
- `clockodo://customers` - Get the list of available customers
- `clockodo://services` - Get the list of available services
- `clockodo://projects` - Get the list of available projects
- `clockodo://recent-entries` - Get recent time entries (last 7 days)

### HR Analytics (when `HR_READONLY` enabled)
- `check_overtime_compliance(year, max_overtime_hours)` - Check employee overtime
- `check_vacation_compliance(year, min_vacation_days, max_vacation_remaining)` - Check vacation usage
- `get_hr_summary(year, ...)` - Complete HR compliance report

### User Tools (when `USER_READ` or `USER_EDIT` enabled)
- `get_my_clock()` - Get currently running clock
- `get_my_time_entries(time_since, time_until)` - Get your time entries
- `start_my_clock(...)` - Start tracking time
- `stop_my_clock()` - Stop tracking time
- `add_my_time_entry(...)` - Add a manual time entry
- `edit_my_time_entry(entry_id, data)` - Edit your time entry
- `delete_my_time_entry(entry_id)` - Delete your time entry
- `add_my_vacation(date_since, date_until)` - Request vacation
- `delete_my_vacation(absence_id)` - Delete vacation request

### Team Leader Tools (when `TEAM_LEADER` enabled)
- `list_pending_vacation_requests(year)` - List all pending vacation requests
- `approve_vacation_request(absence_id)` - Approve a vacation request
- `reject_vacation_request(absence_id)` - Reject a vacation request
- `adjust_vacation_dates(absence_id, new_date_since, new_date_until)` - Adjust vacation length
- `create_team_member_vacation(user_id, date_since, date_until, ...)` - Create vacation for team member
- `edit_team_member_entry(entry_id, data)` - Edit team member's time entry
- `delete_team_member_entry(entry_id)` - Delete team member's time entry

## Development

```bash
# Build
make build-mcp

# Run tests
make test

# Type checking
make type

# Linting
make lint

# Style check
make format-check
```

### Security Scanning

Run comprehensive security scans on the Docker image:

```bash
# Run all security scans (vulnerability, Docker best practices, licenses, SBOM)
make all-scans

# Individual scans
make vulnerability-scan  # Trivy vulnerability scanning
make docker-scan        # Dockle Docker best practices
make license-check      # Python dependency license check
make sbom              # Generate Software Bill of Materials
```

All security tools run via Docker containers - no local installation required.

## Manual Testing

For manual testing with real Clockodo API credentials, use the Jupyter notebook:

```bash
make manual-test
```

Open `http://localhost:8888` and navigate to `work/manual-test/test_clockodo.ipynb`.

See [manual-test/JUPYTER_TESTING.md](manual-test/JUPYTER_TESTING.md) for detailed instructions.

## Project Structure

```
clockodo-mcp/
├── src/clockodo_mcp/
│   ├── server.py              # MCP tool registration
│   ├── client.py              # Clockodo API client
│   ├── config.py              # Feature flag configuration
│   ├── hr_analyzer.py         # Pure data analysis functions
│   ├── services/
│   │   ├── hr_service.py      # Business logic orchestration
│   │   ├── user_service.py    # User operations
│   │   └── team_leader_service.py  # Team leader operations
│   └── tools/
│       ├── hr_tools.py        # MCP tool wrappers
│       ├── user_tools.py      # User tool wrappers
│       ├── team_leader_tools.py    # Team leader tool wrappers
│       └── debug_tools.py     # Debugging utilities
├── tests/                      # Unit and integration tests
├── manual-test/               # Jupyter notebooks for manual testing
├── docker-compose.yml         # Dev and server services
├── docker-compose.test.yml    # Test and Jupyter services
└── makefile                   # Build and test targets
```

## Contributing

When adding new features, follow these patterns:

1. **New API Endpoint**: Add method to `client.py`
2. **Business Logic**: Create/update service in `services/`
3. **MCP Tool**: Add tool registration in `server.py`
4. **Tests**: Add unit tests in `tests/`
5. **Documentation**: Update README and docstrings

Always maintain the layered architecture: Server → Service → Client
