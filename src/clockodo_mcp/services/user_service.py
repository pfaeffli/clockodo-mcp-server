"""
User service for single-user interactions.

This module implements the service layer for user-specific functionality.

Pattern: Service Layer (Layer 2)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from ..date_utils import normalize_datetime

if TYPE_CHECKING:
    from ..client import ClockodoClient


def _check_half_day(
    half_day: bool | None, date_since: str | None, date_until: str | None
) -> None:
    """Clockodo only allows half-day absences on a single day."""
    if half_day and date_since != date_until:
        raise ValueError("A half-day vacation must be a single day")


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
        half_day: bool = False,
    ) -> dict:
        """
        Add a vacation entry for the current user.

        Absence type 1 is usually 'Vacation' in Clockodo. A half day must be a
        single day (date_since == date_until).
        """
        _check_half_day(half_day, date_since, date_until)
        user_id = self.get_current_user_id()
        return self.client.create_absence(
            date_since=date_since,
            date_until=date_until,
            absence_type=1,
            user_id=user_id,
            half_day=half_day,
        )

    def add_my_sick_day(
        self,
        date_since: str,
        date_until: str,
        sick_note: bool = False,
        child: bool = False,
    ) -> dict:
        """
        Add a sick day entry for the current user.

        Absence type 4 is 'Sick day', type 5 is 'Sick day of a child'. Clockodo
        requires the sick_note flag for both, so it is always sent.
        """
        user_id = self.get_current_user_id()
        return self.client.create_absence(
            date_since=date_since,
            date_until=date_until,
            absence_type=5 if child else 4,
            user_id=user_id,
            sick_note=sick_note,
        )

    def edit_my_vacation(
        self,
        absence_id: int,
        date_since: str | None = None,
        date_until: str | None = None,
        half_day: bool | None = None,
    ) -> dict:
        """
        Change the dates or half-day flag of one of the current user's absences.

        Only the given fields are sent. The absence must belong to the current
        user, even if the API key could edit other users' absences.
        """
        fields = {
            "date_since": date_since,
            "date_until": date_until,
            "half_day": half_day,
        }
        changes = {k: v for k, v in fields.items() if v is not None}
        if not changes:
            raise ValueError("Nothing to change: pass dates or half_day")

        absence = self._get_own_absence(absence_id)
        # Clockodo's spec doesn't list half_day on absences; use it if returned
        _check_half_day(
            half_day if half_day is not None else absence.get("half_day"),
            date_since or absence.get("date_since"),
            date_until or absence.get("date_until"),
        )

        return self.client.edit_absence(absence_id, changes)

    def _get_own_absence(self, absence_id: int) -> dict:
        """Fetch an absence and ensure it belongs to the current user."""
        absence = self.client.get_absence(absence_id).get("data") or {}
        if absence.get("users_id") != self.get_current_user_id():
            raise PermissionError(f"Absence {absence_id} is not your absence")
        return absence

    def _get_own_entry(self, entry_id: int) -> dict:
        """Fetch a time entry and ensure it belongs to the current user."""
        entry = self.client.get_entry(entry_id).get("entry") or {}
        if entry.get("users_id") != self.get_current_user_id():
            raise PermissionError(f"Entry {entry_id} is not your entry")
        return entry

    def get_my_absences(self, year: int, absence_type: int | None = None) -> dict:
        """List the authenticated user's absences for a year, optionally by type."""
        user_id = self.get_current_user_id()
        raw = self.client.list_absences(
            year, user_id=user_id, absence_type=absence_type
        )
        return {"absences": raw.get("absences") or []}

    def get_my_entries(self, time_since: str, time_until: str) -> dict:
        """Get time entries for the current user."""
        user_id = self.get_current_user_id()
        return self.client.list_entries(
            time_since=normalize_datetime(time_since),
            time_until=normalize_datetime(time_until),
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
            time_since=normalize_datetime(time_since),
            time_until=normalize_datetime(time_until),
            projects_id=projects_id,
            text=text,
            user_id=user_id,
        )

    def edit_my_entry(self, entry_id: int, data: dict) -> dict:
        """
        Edit one of the current user's time entries.

        The entry must belong to the current user, even if the API key could
        edit other users' entries.
        """
        self._get_own_entry(entry_id)
        return self.client.edit_entry(entry_id, data)

    def delete_my_entry(self, entry_id: int) -> dict:
        """Delete one of the current user's time entries."""
        self._get_own_entry(entry_id)
        return self.client.delete_entry(entry_id)

    def cancel_my_vacation(self, absence_id: int) -> dict:
        """
        Cancel an approved vacation/absence by setting status to 3 (approval cancelled).

        Status transitions:
        - From status 1 (approved) → 3 (approval cancelled)
        - Status 3 can then be deleted

        Note: Status 4 (request cancelled) is only valid from status 0 (enquired).
        The absence must belong to the current user.
        """
        self._get_own_absence(absence_id)
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
              The absence must belong to the current user.
        """
        self._get_own_absence(absence_id)
        if auto_cancel:
            try:
                self.cancel_my_vacation(absence_id)
            # pylint: disable-next=broad-exception-caught
            except (
                httpx.HTTPStatusError,
                Exception,
            ):
                # If cancelling fails (e.g., already cancelled), try deletion anyway
                pass
        return self.client.delete_absence(absence_id)
