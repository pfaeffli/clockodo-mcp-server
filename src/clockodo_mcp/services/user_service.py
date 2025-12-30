"""
User service for single-user interactions.

This module implements the service layer for user-specific functionality.

Pattern: Service Layer (Layer 2)
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import ClockodoClient


class UserService:
    """
    Service for user-specific operations like time tracking and vacations.
    """

    def __init__(self, client: ClockodoClient):
        self.client = client
        self._current_user_id: int | None = None

    def get_current_user_id(self) -> int:
        """
        Get the ID of the current user based on API credentials.
        """
        if self._current_user_id is not None:
            return self._current_user_id

        users_data = self.client.list_users()
        for user in users_data.get("users", []):
            if user.get("email") == self.client.api_user:
                self._current_user_id = user["id"]
                return self._current_user_id

        raise ValueError(f"Could not find user with email {self.client.api_user}")

    def get_my_clock(self) -> dict:
        """Get the currently running clock for the user."""
        return self.client.get_clock()

    def start_my_clock(
        self,
        customers_id: int,
        services_id: int,
        billable: int | None = None,
        projects_id: int | None = None,
        text: str | None = None,
    ) -> dict:
        """Start the clock for the current user."""
        return self.client.clock_start(
            customers_id=customers_id,
            services_id=services_id,
            billable=billable,
            projects_id=projects_id,
            text=text,
        )

    def stop_my_clock(self) -> dict:
        """
        Stop the currently running clock.

        This method automatically fetches the running clock ID and stops it.
        """
        clock_status = self.client.get_clock()
        if clock_status.get("running") and clock_status["running"].get("id"):
            entry_id = clock_status["running"]["id"]
            return self.client.clock_stop(entry_id)
        raise ValueError("No clock is currently running")

    def add_my_vacation(
        self,
        date_since: str,
        date_until: str,
    ) -> dict:
        """
        Add a vacation entry for the current user.

        Absence type 1 is usually 'Vacation' in Clockodo.
        """
        user_id = self.get_current_user_id()
        return self.client.create_absence(
            date_since=date_since,
            date_until=date_until,
            absence_type=1,
            user_id=user_id,
        )

    def get_my_entries(self, time_since: str, time_until: str) -> dict:
        """Get time entries for the current user."""
        user_id = self.get_current_user_id()
        return self.client.list_entries(
            time_since=time_since,
            time_until=time_until,
            user_id=user_id,
        )

    def add_my_entry(
        self,
        customers_id: int,
        services_id: int,
        billable: int,
        time_since: str,
        time_until: str,
        projects_id: int | None = None,
        text: str | None = None,
    ) -> dict:
        """Add a time entry for the current user."""
        user_id = self.get_current_user_id()
        return self.client.create_entry(
            customers_id=customers_id,
            services_id=services_id,
            billable=billable,
            time_since=time_since,
            time_until=time_until,
            projects_id=projects_id,
            text=text,
            user_id=user_id,
        )

    def edit_my_entry(self, entry_id: int, data: dict) -> dict:
        """
        Edit a time entry.
        Note: The API will validate if the user has permission to edit this entry.
        """
        # For security, we could verify if the entry belongs to the user,
        # but Clockodo API handles this based on permissions.
        return self.client.edit_entry(entry_id, data)

    def delete_my_entry(self, entry_id: int) -> dict:
        """Delete a time entry."""
        return self.client.delete_entry(entry_id)

    def cancel_my_vacation(self, absence_id: int) -> dict:
        """
        Cancel an approved vacation/absence by setting status to 3 (approval cancelled).

        Status transitions:
        - From status 1 (approved) → 3 (approval cancelled)
        - Status 3 can then be deleted

        Note: Status 4 (request cancelled) is only valid from status 0 (enquired).
        """
        return self.client.edit_absence(absence_id, {"status": 3})

    def delete_my_vacation(self, absence_id: int, auto_cancel: bool = False) -> dict:
        """
        Delete a vacation/absence.

        Args:
            absence_id: ID of the absence to delete
            auto_cancel: If True, automatically cancel (status=3) before deleting

        Note: Absences must be in status 2 (declined), 3 (approval cancelled),
              or 4 (request cancelled) before deletion.
              This method uses status 3 for approved absences.
        """
        if auto_cancel:
            try:
                self.cancel_my_vacation(absence_id)
            except Exception:
                # If cancelling fails, try deletion anyway
                pass
        return self.client.delete_absence(absence_id)
