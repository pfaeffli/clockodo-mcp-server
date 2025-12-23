# Clockodo MCP Server

MCP server wrapper for the Clockodo time tracking API with configurable feature sets.

## Table of Contents
- [Architecture & Patterns](#architecture--patterns)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Available Tools](#available-tools)
- [Development](#development)
- [Manual Testing](#manual-testing)

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

**Pattern**: Version-Aware Client

```python
def get_user_reports(self, year: int) -> dict:
    """Handle legacy v1 endpoints explicitly"""
    # userreports is v1, not v2
    v1_base_url = self.base_url.replace("/api/v2/", "/api/")
    url = f"{v1_base_url}userreports"
```

**Rules:**
- Default to v2 API base URL
- Explicitly handle v1 endpoints where needed
- Document version differences in code
- Clear URL construction

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

1. Build the Docker image:
   ```bash
   make build
   ```

2. Add configuration to your IDE's MCP settings:

```json
{
  "mcpServers": {
    "clockodo": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "clockodo-mcp:latest"],
      "env": {
        "CLOCKODO_API_USER": "your@email.com",
        "CLOCKODO_API_KEY": "your_api_key",
        "CLOCKODO_USER_AGENT": "my-company/1.0",
        "CLOCKODO_BASE_URL": "https://my.clockodo.com/api/v2/",
        "CLOCKODO_EXTERNAL_APP_CONTACT": "dev@company.com",
        "CLOCKODO_MCP_ENABLE_HR_READONLY": "true",
        "CLOCKODO_MCP_ENABLE_USER_READ": "true",
        "CLOCKODO_MCP_ENABLE_USER_EDIT": "true",
        "CLOCKODO_MCP_ENABLE_ADMIN_READ": "true",
        "CLOCKODO_MCP_ENABLE_ADMIN_EDIT": "true"
      }
    }
  }
}
```

## Environment Variables

### API Credentials (Required)
- `CLOCKODO_API_USER` - Your Clockodo email
- `CLOCKODO_API_KEY` - Your Clockodo API key

### API Configuration (Optional)
- `CLOCKODO_USER_AGENT` - Custom user agent string (default: "clockodo-mcp/unknown")
- `CLOCKODO_BASE_URL` - API base URL (default: "https://my.clockodo.com/api/v2/")
- `CLOCKODO_EXTERNAL_APP_CONTACT` - Contact info for external app header (default: API user email)

### Feature Configuration (Optional)

**Quick Presets:**
- `CLOCKODO_MCP_PRESET=readonly` - HR analytics only (default)
- `CLOCKODO_MCP_PRESET=user` - HR analytics + your own time entries
- `CLOCKODO_MCP_PRESET=admin` - All features

**Granular Flags:**
- `CLOCKODO_MCP_ENABLE_HR_READONLY=true` - HR compliance analytics
- `CLOCKODO_MCP_ENABLE_USER_READ=true` - Read your time entries
- `CLOCKODO_MCP_ENABLE_USER_EDIT=true` - Edit your time entries
- `CLOCKODO_MCP_ENABLE_ADMIN_READ=true` - Read all users' data
- `CLOCKODO_MCP_ENABLE_ADMIN_EDIT=true` - Edit all users' data

## Available Tools

- `health` - Health check (shows enabled features)
- `list_users` - List all Clockodo users
- `get_raw_user_reports(year)` - Get raw API response for debugging
- `check_overtime_compliance(year, max_overtime_hours)` - Check employee overtime
- `check_vacation_compliance(year, min_vacation_days, max_vacation_remaining)` - Check vacation usage
- `get_hr_summary(year, ...)` - Complete HR compliance report

## Development

```bash
# Build
make build

# Run tests
docker-compose -f docker-compose.test.yml run --rm test

# Type checking
docker-compose -f docker-compose.test.yml run --rm type

# Linting
docker-compose -f docker-compose.test.yml run --rm lint

# Style check
docker-compose -f docker-compose.test.yml run --rm style-check
```

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
│   │   └── hr_service.py      # Business logic orchestration
│   └── tools/
│       ├── hr_tools.py        # MCP tool wrappers
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
