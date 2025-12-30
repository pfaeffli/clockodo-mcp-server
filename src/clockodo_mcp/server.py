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
from .tools import debug_tools, hr_tools, user_tools

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
def list_customers() -> dict:
    """List all customers from Clockodo API."""
    client = ClockodoClient.from_env()
    return client.list_customers()


@mcp.tool()
def list_services() -> dict:
    """List all services from Clockodo API."""
    client = ClockodoClient.from_env()
    return client.list_services()


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

        @mcp.tool()
        def get_my_clock() -> dict:
            """Get the currently running clock for the authenticated user."""
            return user_tools.get_my_clock()

        @mcp.tool()
        def get_my_time_entries(time_since: str, time_until: str) -> dict:
            """
            Get time entries for the authenticated user in a given time range.

            Args:
                time_since: Start time (e.g., 2025-01-01 00:00:00)
                time_until: End time (e.g., 2025-01-01 23:59:59)
            """
            return user_tools.get_my_entries(time_since, time_until)

    # User Edit Tools
    if config.is_enabled(FeatureGroup.USER_EDIT):

        @mcp.tool()
        def start_my_clock(
            customers_id: int,
            services_id: int,
            billable: int = 1,
            projects_id: int | None = None,
            text: str | None = None,
        ) -> dict:
            """
            Start the clock for the authenticated user.

            Args:
                customers_id: ID of the customer
                services_id: ID of the service
                billable: Whether the entry is billable (1) or not (0)
                projects_id: Optional project ID
                text: Optional description
            """
            return user_tools.start_my_clock(
                customers_id=customers_id,
                services_id=services_id,
                billable=billable,
                projects_id=projects_id,
                text=text,
            )

        @mcp.tool()
        def stop_my_clock() -> dict:
            """Stop the currently running clock for the authenticated user."""
            return user_tools.stop_my_clock()

        @mcp.tool()
        def add_my_vacation(date_since: str, date_until: str) -> dict:
            """
            Add a vacation for the authenticated user.

            Args:
                date_since: Start date (YYYY-MM-DD)
                date_until: End date (YYYY-MM-DD)
            """
            return user_tools.add_my_vacation(date_since, date_until)

        @mcp.tool()
        def add_my_time_entry(
            customers_id: int,
            services_id: int,
            time_since: str,
            time_until: str,
            billable: int = 1,
            projects_id: int | None = None,
            text: str | None = None,
        ) -> dict:
            """
            Add a manual time entry for the authenticated user.

            Args:
                customers_id: ID of the customer
                services_id: ID of the service
                time_since: Start time (e.g., 2025-01-01 09:00:00)
                time_until: End time (e.g., 2025-01-01 10:00:00)
                billable: Whether the entry is billable (1) or not (0)
                projects_id: Optional project ID
                text: Optional description
            """
            return user_tools.add_my_entry(
                customers_id=customers_id,
                services_id=services_id,
                time_since=time_since,
                time_until=time_until,
                billable=billable,
                projects_id=projects_id,
                text=text,
            )

        @mcp.tool()
        def edit_my_time_entry(entry_id: int, data: dict) -> dict:
            """
            Edit a time entry for the authenticated user.

            Args:
                entry_id: ID of the entry to edit
                data: Dictionary of fields to update (e.g., {"text": "new description"})
            """
            return user_tools.edit_my_entry(entry_id, data)

        @mcp.tool()
        def delete_my_time_entry(entry_id: int) -> dict:
            """
            Delete a time entry for the authenticated user.

            Args:
                entry_id: ID of the entry to delete
            """
            return user_tools.delete_my_entry(entry_id)

        @mcp.tool()
        def delete_my_vacation(absence_id: int) -> dict:
            """
            Delete a vacation/absence for the authenticated user.

            Args:
                absence_id: ID of the absence to delete
            """
            return user_tools.delete_my_vacation(absence_id)

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
            self.tools = {
                "list_users": lambda: client.list_users() if client else {},
                "list_customers": lambda: client.list_customers() if client else {},
                "list_services": lambda: client.list_services() if client else {},
            }
            self.tool_names = ["health", "list_users", "list_customers", "list_services"]

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
                self.tool_names.extend(["add_my_time_entry", "delete_my_vacation"])
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
