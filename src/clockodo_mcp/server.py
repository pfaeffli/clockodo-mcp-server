"""
Clockodo MCP Server - Main entry point and tool registration.

This module implements the MCP server layer.

Pattern: Server Layer (Layer 1)
- Only handles MCP tool registration
- No business logic (delegates to services)
- No HTTP communication (delegates to client)
- Uses configuration to enable/disable features

Architecture: Server → Service → Client
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore

from .client import ClockodoClient
from .config import FeatureGroup, ServerConfig
from .tools import debug_tools, hr_tools

# Pattern #2: Configuration Management
# Load configuration from environment variables with safe defaults
config = ServerConfig.from_env()

# Create MCP server instance
mcp = FastMCP("clockodo")


@mcp.tool()
def health() -> dict[str, str | list[str]]:
    """Health check for the Clockodo MCP server."""
    return {
        "status": "ok",
        "enabled_features": config.get_enabled_features(),
    }


@mcp.tool()
def list_users() -> dict:
    """List all users from Clockodo API."""
    client = ClockodoClient.from_env()
    return client.list_users()


@mcp.tool()
def get_raw_user_reports(year: int) -> dict:
    """
    Get raw user reports from Clockodo API (for debugging).

    Shows the actual data returned by Clockodo's /api/userreports endpoint.

    Args:
        year: Year to fetch (e.g., 2024, 2025)

    Returns:
        Raw API response with all user report data
    """
    return debug_tools.get_raw_user_reports(year)


# ==============================================
# Conditional Tool Registration
# ==============================================


def register_tools():
    """
    Register MCP tools based on enabled features.

    Follows Pattern #10 (Environment-Based Behavior):
    - Feature flags control which tools are registered
    - No if/else for environments
    - Configuration over code
    """

    # HR Tools (Read-only)
    if config.is_enabled(FeatureGroup.HR_READONLY):

        @mcp.tool()
        def check_overtime_compliance(
            year: int, max_overtime_hours: float = 80
        ) -> dict:
            """
            Check which employees have excessive overtime.

            Args:
                year: Year to check (e.g., 2024)
                max_overtime_hours: Maximum allowed overtime hours (default: 80)

            Returns:
                Dictionary with overtime violations
            """
            return hr_tools.check_overtime_compliance(year, max_overtime_hours)

        @mcp.tool()
        def check_vacation_compliance(
            year: int, min_vacation_days: float = 10, max_vacation_remaining: float = 20
        ) -> dict:
            """
            Check which employees have vacation compliance issues.

            Args:
                year: Year to check (e.g., 2024)
                min_vacation_days: Minimum vacation days that should be used (default: 10)
                max_vacation_remaining: Maximum vacation days that can remain unused (default: 20)

            Returns:
                Dictionary with vacation violations
            """
            return hr_tools.check_vacation_compliance(
                year, min_vacation_days, max_vacation_remaining
            )

        @mcp.tool()
        def get_hr_summary(
            year: int,
            max_overtime_hours: float = 80,
            min_vacation_days: float = 10,
            max_vacation_remaining: float = 20,
        ) -> dict:
            """
            Get complete HR compliance summary for all employees.

            Args:
                year: Year to check (e.g., 2024)
                max_overtime_hours: Maximum allowed overtime hours (default: 80)
                min_vacation_days: Minimum vacation days that should be used (default: 10)
                max_vacation_remaining: Maximum vacation days that can remain unused (default: 20)

            Returns:
                Dictionary with complete HR summary including all violations
            """
            return hr_tools.get_hr_summary(
                year, max_overtime_hours, min_vacation_days, max_vacation_remaining
            )

    # User Read Tools
    if config.is_enabled(FeatureGroup.USER_READ):
        # Placeholder for user read tools
        @mcp.tool()
        def get_my_time_entries(start_date: str, end_date: str) -> dict:
            """Get time entries for current user (placeholder)."""
            return {
                "message": "User read tools coming soon",
                "start_date": start_date,
                "end_date": end_date,
            }

    # User Edit Tools
    if config.is_enabled(FeatureGroup.USER_EDIT):
        # Placeholder for user edit tools
        @mcp.tool()
        def add_my_time_entry(date: str, hours: float, description: str) -> dict:
            """Add time entry for current user (placeholder)."""
            return {
                "message": "User edit tools coming soon",
                "date": date,
                "hours": hours,
            }

    # Admin Read Tools
    if config.is_enabled(FeatureGroup.ADMIN_READ):
        # Placeholder for admin read tools
        @mcp.tool()
        def get_all_time_entries(user_id: int, start_date: str, end_date: str) -> dict:
            """Get time entries for any user (admin, placeholder)."""
            return {"message": "Admin read tools coming soon", "user_id": user_id}

    # Admin Edit Tools
    if config.is_enabled(FeatureGroup.ADMIN_EDIT):
        # Placeholder for admin edit tools
        @mcp.tool()
        def edit_user_time_entry(entry_id: int, hours: float) -> dict:
            """Edit any user's time entry (admin, placeholder)."""
            return {"message": "Admin edit tools coming soon", "entry_id": entry_id}


def create_server(client=None, test_config: ServerConfig | None = None):
    """Create server for testing purposes."""
    # This is a stub for testing - actual server uses mcp global
    test_conf = test_config or config

    class MockServer:
        def __init__(self):
            self.config = test_conf
            self.tools = {"list_users": lambda: client.list_users() if client else {}}
            self.tool_names = ["health", "list_users"]

            # Add tool names based on config
            if test_conf.hr_readonly:
                self.tool_names.extend(
                    [
                        "check_overtime_compliance",
                        "check_vacation_compliance",
                        "get_hr_summary",
                    ]
                )
            if test_conf.user_read:
                self.tool_names.append("get_my_time_entries")
            if test_conf.user_edit:
                self.tool_names.append("add_my_time_entry")
            if test_conf.admin_read:
                self.tool_names.append("get_all_time_entries")
            if test_conf.admin_edit:
                self.tool_names.append("edit_user_time_entry")

    return MockServer()


# Register tools on module load
register_tools()


def main() -> None:
    """Run the MCP server using stdio transport."""
    mcp.run(transport="stdio")
