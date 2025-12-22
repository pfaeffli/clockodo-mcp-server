# Clockodo MCP Server

MCP server wrapper for the Clockodo time tracking API with configurable feature sets.

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
- `check_overtime_compliance(year, max_overtime_hours)` - Check employee overtime
- `check_vacation_compliance(year, min_vacation_days, max_vacation_remaining)` - Check vacation usage
- `get_hr_summary(year, ...)` - Complete HR compliance report

## Development

```bash
# Build
make build

# Run tests
docker compose run --rm dev pytest tests/ -v

# Local development with .env file
cp .env.example .env
docker-compose up server
```
