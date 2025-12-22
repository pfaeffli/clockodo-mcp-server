# Clockodo MCP Server

MCP server wrapper for the Clockodo time tracking API.

## Configuration

Create a `.env` file with your Clockodo credentials:

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

## Build the Docker Image

```bash
make build
```

Or using docker-compose:

```bash
docker-compose build server
```

## Running the Server

```bash
docker-compose up server
```

## PyCharm/IntelliJ MCP Configuration

First, build the image using `make build`.

Then add this configuration to your IDE's MCP settings:

```json
{
  "mcpServers": {
    "clockodo": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file",
        "~/.config/clockodo-mcp/.env",
        "clockodo-mcp:latest"
      ]
    }
  }
}
```

Replace `/absolute/path/to/clockodo-mcp/.env` with the actual path to your `.env` file.

## Available Tools

### General
- `health` - Health check endpoint
- `list_users` - Fetch list of users from Clockodo API

### HR Automation
- `check_overtime_compliance(year, max_overtime_hours=80)` - Check which employees have excessive overtime
  - Returns list of employees exceeding the overtime threshold
- `check_vacation_compliance(year, min_vacation_days=10, max_vacation_remaining=20)` - Check vacation compliance
  - Identifies employees who haven't taken enough vacation or have too many days remaining
- `get_hr_summary(year, max_overtime_hours=80, min_vacation_days=10, max_vacation_remaining=20)` - Complete HR report
  - Returns comprehensive summary of all HR compliance issues for all employees

### Example Usage

```python
# Check overtime for 2024
check_overtime_compliance(year=2024, max_overtime_hours=80)

# Check vacation compliance
check_vacation_compliance(year=2024, min_vacation_days=10, max_vacation_remaining=15)

# Get complete HR summary
get_hr_summary(year=2024)
```
