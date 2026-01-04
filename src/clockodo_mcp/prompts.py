"""
MCP Prompts for Clockodo Server.

Provides interactive prompt templates for common time tracking workflows.
"""

from __future__ import annotations


def get_start_work_prompt(
    customer: str, service: str, project: str | None = None
) -> str:
    """
    Generate a prompt to start tracking work time.

    Args:
        customer: Customer name
        service: Service/task name
        project: Optional project name

    Returns:
        Formatted prompt string
    """
    if project:
        return (
            f"Start tracking time for customer '{customer}', "
            f"project '{project}', service '{service}'"
        )
    return f"Start tracking time for customer '{customer}', service '{service}'"


def get_stop_work_prompt() -> str:
    """Generate a prompt to stop tracking time."""
    return "Stop tracking time for the current task"


def get_add_time_entry_prompt(
    customer: str,
    service: str,
    date: str,
    duration_hours: float,
    description: str | None = None,
) -> str:
    """
    Generate a prompt to add a manual time entry.

    Args:
        customer: Customer name
        service: Service/task name
        date: Date for the entry (YYYY-MM-DD)
        duration_hours: Duration in hours
        description: Optional description

    Returns:
        Formatted prompt string
    """
    prompt = (
        f"Add a time entry for {duration_hours} hours on {date} "
        f"for customer '{customer}', service '{service}'"
    )
    if description:
        prompt += f" with description: {description}"
    return prompt


def get_vacation_request_prompt(start_date: str, end_date: str) -> str:
    """
    Generate a prompt to request vacation.

    Args:
        start_date: Vacation start date (YYYY-MM-DD)
        end_date: Vacation end date (YYYY-MM-DD)

    Returns:
        Formatted prompt string
    """
    return f"Request vacation from {start_date} to {end_date}"


def get_check_overtime_prompt(year: int) -> str:
    """
    Generate a prompt to check overtime compliance.

    Args:
        year: Year to check (e.g., 2024)

    Returns:
        Formatted prompt string
    """
    return f"Check overtime compliance for all employees in {year}"


def get_approve_vacation_prompt(employee_name: str, date_range: str) -> str:
    """
    Generate a prompt to approve a vacation request.

    Args:
        employee_name: Name of the employee
        date_range: Date range string (e.g., "2024-12-20 to 2024-12-31")

    Returns:
        Formatted prompt string
    """
    return f"Approve vacation request for {employee_name} ({date_range})"
