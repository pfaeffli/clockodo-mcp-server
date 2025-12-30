"""MCP tools for user-specific interactions."""

from __future__ import annotations
from ..client import ClockodoClient
from ..services.user_service import UserService


def get_my_clock() -> dict:
    """Get the currently running clock for the authenticated user."""
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.get_my_clock()


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
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.start_my_clock(
        customers_id=customers_id,
        services_id=services_id,
        billable=billable,
        projects_id=projects_id,
        text=text,
    )


def stop_my_clock() -> dict:
    """Stop the currently running clock for the authenticated user."""
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.stop_my_clock()


def add_my_vacation(date_since: str, date_until: str) -> dict:
    """
    Add a vacation for the authenticated user.

    Args:
        date_since: Start date (YYYY-MM-DD)
        date_until: End date (YYYY-MM-DD)
    """
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.add_my_vacation(date_since, date_until)


def get_my_entries(time_since: str, time_until: str) -> dict:
    """
    Get time entries for the authenticated user in a given time range.

    Args:
        time_since: Start time (e.g., 2025-01-01 00:00:00)
        time_until: End time (e.g., 2025-01-01 23:59:59)
    """
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.get_my_entries(time_since, time_until)


def add_my_entry(
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
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.add_my_entry(
        customers_id=customers_id,
        services_id=services_id,
        time_since=time_since,
        time_until=time_until,
        billable=billable,
        projects_id=projects_id,
        text=text,
    )


def edit_my_entry(entry_id: int, data: dict) -> dict:
    """
    Edit a time entry for the authenticated user.

    Args:
        entry_id: ID of the entry to edit
        data: Dictionary of fields to update (e.g., {"text": "new description"})
    """
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.edit_my_entry(entry_id, data)


def delete_my_entry(entry_id: int) -> dict:
    """
    Delete a time entry for the authenticated user.

    Args:
        entry_id: ID of the entry to delete
    """
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.delete_my_entry(entry_id)


def delete_my_vacation(absence_id: int) -> dict:
    """
    Delete a vacation/absence for the authenticated user.

    Args:
        absence_id: ID of the absence to delete
    """
    client = ClockodoClient.from_env()
    service = UserService(client)
    return service.delete_my_vacation(absence_id)
