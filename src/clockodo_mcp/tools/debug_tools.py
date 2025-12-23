"""Debug tools to inspect raw API responses."""
from __future__ import annotations

from ..client import ClockodoClient


def get_raw_user_reports(year: int) -> dict:
    """
    Get raw user reports data from Clockodo API (for debugging).

    Args:
        year: Year to check (e.g., 2024)

    Returns:
        Raw API response from /api/userreports endpoint
    """
    client = ClockodoClient.from_env()
    return client.get_user_reports(year=year)
