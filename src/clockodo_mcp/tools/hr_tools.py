"""MCP tools for HR compliance checking."""

from __future__ import annotations

from ..client import ClockodoClient
from ..services.hr_service import HRService


def check_overtime_compliance(year: int, max_overtime_hours: float = 80) -> dict:
    """
    Check which employees have excessive overtime.

    Args:
        year: Year to check (e.g., 2024)
        max_overtime_hours: Maximum allowed overtime hours (default: 80)

    Returns:
        Dictionary with overtime violations
    """
    client = ClockodoClient.from_env()
    service = HRService(client)
    return service.check_overtime_compliance(year, max_overtime_hours)


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
    client = ClockodoClient.from_env()
    service = HRService(client)
    return service.check_vacation_compliance(
        year, min_vacation_days, max_vacation_remaining
    )


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
    client = ClockodoClient.from_env()
    service = HRService(client)
    return service.get_hr_summary(
        year, max_overtime_hours, min_vacation_days, max_vacation_remaining
    )
