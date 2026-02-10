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

import json

from mcp.server.fastmcp import FastMCP  # type: ignore

from . import prompts as prompt_templates
from . import resources as resource_handlers
from .client import ClockodoClient
from .config import FeatureGroup, ServerConfig
from .services.team_leader_service import TeamLeaderService
from .tools import debug_tools, hr_tools, team_leader_tools, user_tools

# Pattern #2: Configuration Management
# Load configuration from environment variables with safe defaults
config = ServerConfig.from_env()

# Create MCP server instance with configured host and port
mcp = FastMCP("clockodo", host=config.host, port=config.port)


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
def list_projects() -> dict:
    """List all projects from Clockodo API."""
    client = ClockodoClient.from_env()
    return client.list_projects()


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
# MCP Prompts
# ==============================================


@mcp.prompt()
def start_tracking(customer: str, service: str, project: str = "") -> str:
    """
    Start tracking time for a customer and service.

    Args:
        customer: Customer name
        service: Service/task name
        project: Optional project name
    """
    return prompt_templates.get_start_work_prompt(
        customer, service, project if project else None
    )


@mcp.prompt()
def stop_tracking() -> str:
    """Stop tracking the current time entry."""
    return prompt_templates.get_stop_work_prompt()


@mcp.prompt()
def request_vacation(start_date: str, end_date: str) -> str:
    """
    Request vacation time.

    Args:
        start_date: Vacation start date (YYYY-MM-DD)
        end_date: Vacation end date (YYYY-MM-DD)
    """
    return prompt_templates.get_vacation_request_prompt(start_date, end_date)


# ==============================================
# MCP Resources
# ==============================================


@mcp.resource("clockodo://current-entry")
def current_entry() -> str:
    """Get the currently running time entry."""
    resource = resource_handlers.get_current_time_entry_resource()
    return json.dumps(resource["content"], indent=2)


@mcp.resource("clockodo://customers")
def customers_list() -> str:
    """Get the list of available customers."""
    resource = resource_handlers.get_customers_resource()
    return json.dumps(resource["content"], indent=2)


@mcp.resource("clockodo://services")
def services_list() -> str:
    """Get the list of available services."""
    resource = resource_handlers.get_services_resource()
    return json.dumps(resource["content"], indent=2)


@mcp.resource("clockodo://projects")
def projects_list() -> str:
    """Get the list of available projects."""
    resource = resource_handlers.get_projects_resource()
    return json.dumps(resource["content"], indent=2)


@mcp.resource("clockodo://recent-entries")
def recent_entries() -> str:
    """Get recent time entries (last 7 days)."""
    resource = resource_handlers.get_recent_entries_resource(days=7)
    return json.dumps(resource["content"], indent=2)


# ==============================================
# Conditional Tool Registration
# ==============================================


def _register_hr_tools():
    """Register HR tools."""

    @mcp.tool()
    def check_overtime_compliance(year: int, max_overtime_hours: float = 80) -> dict:
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


def _register_user_read_tools():
    """Register user read tools."""

    @mcp.tool()
    def get_my_clock() -> dict:
        """Get the currently running clock for the authenticated user."""
        return user_tools.get_my_clock()

    @mcp.tool()
    def get_my_time_entries(time_since: str, time_until: str) -> dict:
        """
        Get time entries for the authenticated user in a given time range.

        Args:
            time_since: Start time (e.g., 2025-01-01T00:00:00Z)
            time_until: End time (e.g., 2025-01-01T23:59:59Z)
        """
        return user_tools.get_my_entries(time_since, time_until)


def _register_user_edit_tools():
    """Register user edit tools."""

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
            time_since: Start time (e.g., 2025-01-01T09:00:00Z)
            time_until: End time (e.g., 2025-01-01T10:00:00Z)
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
        _register_hr_tools()

    # User Read Tools
    if config.is_enabled(FeatureGroup.USER_READ):
        _register_user_read_tools()

    # User Edit Tools
    if config.is_enabled(FeatureGroup.USER_EDIT):
        _register_user_edit_tools()

    # Team Leader Tools
    if config.is_enabled(FeatureGroup.TEAM_LEADER):
        # Use lazy client initialization to avoid crashes on invalid credentials
        team_leader_service = TeamLeaderService(ClockodoClient.from_env)
        team_leader_tools.register_team_leader_tools(mcp, team_leader_service)

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
                "list_projects": lambda: client.list_projects() if client else {},
            }
            self.tool_names = [
                "health",
                "list_users",
                "list_customers",
                "list_services",
                "list_projects",
            ]

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
            if test_conf.team_leader:
                self.tool_names.extend(
                    [
                        "list_pending_vacation_requests",
                        "approve_vacation_request",
                        "reject_vacation_request",
                        "adjust_vacation_dates",
                        "create_team_member_vacation",
                        "edit_team_member_entry",
                        "delete_team_member_entry",
                    ]
                )
            if test_conf.admin_read:
                self.tool_names.append("get_all_time_entries")
            if test_conf.admin_edit:
                self.tool_names.append("edit_user_time_entry")

    return MockServer()


# Register tools on module load
register_tools()


def main() -> None:
    """Run the MCP server using configured transport."""
    if config.transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
