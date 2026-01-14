"""
Team leader service for team management operations.

This module implements the service layer for team leader functionality,
including vacation approval/rejection and team member entry modifications.

Pattern: Service Layer (Layer 2)
- Business logic orchestration
- Uses client for API calls
- No MCP-specific code
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..client import ClockodoClient


class TeamLeaderService:
    """
    Service for team leader operations like vacation approval and team edits.

    Team leaders can:
    - Approve/reject vacation requests
    - Edit team members' time entries
    - Adjust vacation days or use overtime
    """

    def __init__(self, client_factory: Callable[[], ClockodoClient]):
        """
        Initialize with a client factory for lazy initialization.

        Args:
            client_factory: Callable that returns a ClockodoClient instance
        """
        self._client_factory = client_factory
        self._client: ClockodoClient | None = None

    @property
    def client(self) -> ClockodoClient:
        """Lazy-load the client on first access."""
        if self._client is None:
            self._client = self._client_factory()
        return self._client

    def approve_vacation(self, absence_id: int) -> dict:
        """
        Approve a vacation/absence request.

        Transitions from status 0 (enquired) → 1 (approved)

        Args:
            absence_id: ID of the absence to approve

        Returns:
            Updated absence data from API
        """
        return self.client.edit_absence(absence_id, {"status": 1})

    def reject_vacation(self, absence_id: int) -> dict:
        """
        Reject a vacation/absence request.

        Transitions from status 0 (enquired) → 2 (declined)

        Args:
            absence_id: ID of the absence to reject

        Returns:
            Updated absence data from API
        """
        return self.client.edit_absence(absence_id, {"status": 2})

    def list_pending_vacations(self, year: int) -> list[dict]:
        """
        List all pending vacation requests (status 0: enquired).

        Args:
            year: Year to filter vacations

        Returns:
            List of pending absence dictionaries
        """
        absences_data = self.client.list_absences(year)
        absences = absences_data.get("absences", [])
        # Status 0 = enquired (pending approval)
        return [a for a in absences if a.get("status") == 0]

    def edit_team_entry(self, entry_id: int, data: dict) -> dict:
        """
        Edit a team member's time entry.

        As a team leader, you can modify entries for your team members.

        Args:
            entry_id: ID of the entry to edit
            data: Dictionary with fields to update (e.g., time_since, time_until, text)

        Returns:
            Updated entry data from API
        """
        return self.client.edit_entry(entry_id, data)

    def delete_team_entry(self, entry_id: int) -> dict:
        """
        Delete a team member's time entry.

        Args:
            entry_id: ID of the entry to delete

        Returns:
            API response confirming deletion
        """
        return self.client.delete_entry(entry_id)

    def adjust_vacation_length(
        self,
        absence_id: int,
        new_date_since: str,
        new_date_until: str,
    ) -> dict:
        """
        Adjust the length of a vacation/absence.

        Useful for partial approval or corrections.

        Args:
            absence_id: ID of the absence to adjust
            new_date_since: New start date (YYYY-MM-DD)
            new_date_until: New end date (YYYY-MM-DD)

        Returns:
            Updated absence data from API
        """
        return self.client.edit_absence(
            absence_id,
            {
                "date_since": new_date_since,
                "date_until": new_date_until,
            },
        )

    def create_team_vacation(
        self,
        user_id: int,
        date_since: str,
        date_until: str,
        absence_type: int = 1,
        auto_approve: bool = False,
    ) -> dict:
        """
        Create a vacation entry for a team member.

        Args:
            user_id: User ID of the team member
            date_since: Start date (YYYY-MM-DD)
            date_until: End date (YYYY-MM-DD)
            absence_type: Type of absence (1: Vacation, 2: Illness, etc.)
            auto_approve: If True, set status to 1 (approved) immediately

        Returns:
            Created absence data from API
        """
        status = 1 if auto_approve else 0  # 0=enquired, 1=approved
        return self.client.create_absence(
            date_since=date_since,
            date_until=date_until,
            absence_type=absence_type,
            user_id=user_id,
            status=status,
        )
