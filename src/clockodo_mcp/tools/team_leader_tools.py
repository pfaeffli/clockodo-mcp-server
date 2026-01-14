"""
MCP tools for team leader functionality.

This module registers MCP tools for team leader operations.

Pattern: Tool Layer (Layer 1)
- Thin wrappers around service calls
- MCP-specific only
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.team_leader_service import TeamLeaderService


def register_team_leader_tools(mcp, service: TeamLeaderService):
    """
    Register all team leader tools with the MCP server.

    Args:
        mcp: MCP server instance
        service: TeamLeaderService instance
    """

    @mcp.tool()
    def list_pending_vacation_requests(year: int) -> list[dict]:
        """
        List all pending vacation requests awaiting approval.

        This shows all vacation requests with status 0 (enquired).
        As a team leader, you can approve or reject these requests.

        Args:
            year: Year to filter vacation requests (e.g., 2024)

        Returns:
            List of pending absence dictionaries with user info, dates, and type
        """
        return service.list_pending_vacations(year)

    @mcp.tool()
    def approve_vacation_request(absence_id: int) -> dict:
        """
        Approve a pending vacation/absence request.

        This changes the status from 0 (enquired) to 1 (approved).

        Args:
            absence_id: ID of the absence to approve

        Returns:
            Updated absence data with new status
        """
        return service.approve_vacation(absence_id)

    @mcp.tool()
    def reject_vacation_request(absence_id: int) -> dict:
        """
        Reject a pending vacation/absence request.

        This changes the status from 0 (enquired) to 2 (declined).

        Args:
            absence_id: ID of the absence to reject

        Returns:
            Updated absence data with new status
        """
        return service.reject_vacation(absence_id)

    @mcp.tool()
    def adjust_vacation_dates(
        absence_id: int,
        new_date_since: str,
        new_date_until: str,
    ) -> dict:
        """
        Adjust the dates of a vacation/absence request.

        Useful for partial approvals or corrections.
        Dates should be in YYYY-MM-DD format.

        Args:
            absence_id: ID of the absence to adjust
            new_date_since: New start date (YYYY-MM-DD)
            new_date_until: New end date (YYYY-MM-DD)

        Returns:
            Updated absence data with new dates
        """
        return service.adjust_vacation_length(
            absence_id, new_date_since, new_date_until
        )

    @mcp.tool()
    def create_team_member_vacation(
        user_id: int,
        date_since: str,
        date_until: str,
        absence_type: int = 1,
        auto_approve: bool = True,
    ) -> dict:
        """
        Create a vacation entry for a team member.

        As a team leader, you can create vacation entries on behalf of team members.
        By default, these are auto-approved (status=1).

        Args:
            user_id: User ID of the team member
            date_since: Start date (YYYY-MM-DD)
            date_until: End date (YYYY-MM-DD)
            absence_type: Type of absence (1=Vacation, 2=Illness, 3=Special leave, etc.)
            auto_approve: If True, approve immediately (default: True)

        Returns:
            Created absence data
        """
        return service.create_team_vacation(
            user_id=user_id,
            date_since=date_since,
            date_until=date_until,
            absence_type=absence_type,
            auto_approve=auto_approve,
        )

    @mcp.tool()
    def edit_team_member_entry(entry_id: int, data: dict) -> dict:
        """
        Edit a time entry for a team member.

        As a team leader, you can modify time entries for your team members.
        Common fields to update: time_since, time_until, text, billable, customers_id, services_id

        Args:
            entry_id: ID of the entry to edit
            data: Dictionary with fields to update
                  Example: {"time_since": "2024-01-15T09:00:00Z", "time_until": "2024-01-15T17:00:00Z"}

        Returns:
            Updated entry data
        """
        return service.edit_team_entry(entry_id, data)

    @mcp.tool()
    def delete_team_member_entry(entry_id: int) -> dict:
        """
        Delete a time entry for a team member.

        Args:
            entry_id: ID of the entry to delete

        Returns:
            API response confirming deletion
        """
        return service.delete_team_entry(entry_id)
