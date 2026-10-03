"""
Build the payload for editing a time entry from explicit parameters.

Shared by the user and team leader services. ``users_id`` is deliberately not
a parameter, so an edit can never move an entry to another user.
"""

from __future__ import annotations

from ..date_utils import normalize_datetime

_BILLABLE_VALUES = (0, 1, 2)


def build_entry_changes(  # pylint: disable=too-many-arguments
    *,
    time_since: str | None = None,
    time_until: str | None = None,
    text: str | None = None,
    customers_id: int | None = None,
    services_id: int | None = None,
    projects_id: int | None = None,
    billable: int | None = None,
) -> dict:
    """Return the payload for the params that were passed (not None)."""
    if billable is not None and billable not in _BILLABLE_VALUES:
        raise ValueError("billable must be 0, 1 or 2")
    candidates: dict = {
        "time_since": normalize_datetime(time_since),
        "time_until": normalize_datetime(time_until),
        "text": text,
        "customers_id": customers_id,
        "services_id": services_id,
        "projects_id": projects_id,
        "billable": billable,
    }
    changes = {key: value for key, value in candidates.items() if value is not None}
    if not changes:
        raise ValueError("Pass at least one field to change")
    return changes
