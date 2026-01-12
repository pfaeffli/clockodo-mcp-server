# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| main    | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Report security vulnerabilities by creating a [private security advisory](https://github.com/pfaeffli/clockodo-mcp-server/security/advisories/new).

Include:
- Type of issue and impact
- Steps to reproduce
- Affected source code location

You should receive an acknowledgment within 48 hours.

## Security Overview

### Credentials & Secrets
- API credentials via environment variables only (never hardcoded)
- Credentials are not logged
- Docker images do not contain secrets

### Transport Security

**stdio (default)**: No network exposure - safe for local use with Claude Desktop/IDEs

**sse (HTTP/SSE)**: For remote access - requires additional security:
- Deploy behind reverse proxy with HTTPS (nginx, Caddy, Traefik)
- Implement authentication (OAuth, JWT, API keys)
- Add rate limiting and firewall rules

⚠️ **Warning**: SSE mode has no built-in authentication. Must run behind authenticated reverse proxy.

### Role-Based Access Control

- `employee` - Own time entries only
- `team_leader` - Employee + team management
- `hr_analytics` - Read-only HR reports
- `admin` - Full access

Use least privilege principle.

### Security Best Practices

**Environment Variables:**
- Never commit `.env` files with real credentials
- Use secrets management in production
- Rotate API keys regularly

**SSE Deployment:**
```bash
# Only expose to localhost, use reverse proxy for external access
docker run -d \
  -p 127.0.0.1:8000:8000 \
  -e CLOCKODO_API_USER=your@email.com \
  -e CLOCKODO_API_KEY=your_api_key \
  -e CLOCKODO_MCP_ROLE=employee \
  -e CLOCKODO_MCP_TRANSPORT=sse \
  ghcr.io/pfaeffli/clockodo-mcp-server:latest
```

### Security Scanning

Run security scans locally:
```bash
make all-scans  # Vulnerability, Docker, license, and SBOM scans
```

**Note on Trivy Findings**: GitHub Security tab may show LOW/MEDIUM vulnerabilities in base OS packages (util-linux, sqlite, tar, etc.). These are:
- From Debian base image, not our Python code
- Not exploitable in containerized Python applications
- Filtered via `.trivyignore` for HIGH/CRITICAL focus
- All Python dependencies are clean (0 vulnerabilities)

## Known Limitations

- No built-in authentication for SSE transport
- No built-in rate limiting
- No built-in audit trail
