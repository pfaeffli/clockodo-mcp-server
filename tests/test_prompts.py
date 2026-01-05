"""
Tests for prompts.py module.
"""

from clockodo_mcp import prompts


def test_get_start_work_prompt_without_project():
    """Test start work prompt without project."""
    result = prompts.get_start_work_prompt("ACME Corp", "Development")
    assert "ACME Corp" in result
    assert "Development" in result
    assert "Start tracking time" in result


def test_get_start_work_prompt_with_project():
    """Test start work prompt with project."""
    result = prompts.get_start_work_prompt(
        "ACME Corp", "Development", "Website Redesign"
    )
    assert "ACME Corp" in result
    assert "Development" in result
    assert "Website Redesign" in result
    assert "Start tracking time" in result


def test_get_stop_work_prompt():
    """Test stop work prompt."""
    result = prompts.get_stop_work_prompt()
    assert "Stop tracking time" in result
    assert "current task" in result


def test_get_add_time_entry_prompt_without_description():
    """Test add time entry prompt without description."""
    result = prompts.get_add_time_entry_prompt(
        "ACME Corp", "Development", "2024-01-15", 2.5
    )
    assert "ACME Corp" in result
    assert "Development" in result
    assert "2024-01-15" in result
    assert "2.5 hours" in result
    assert "Add a time entry" in result


def test_get_add_time_entry_prompt_with_description():
    """Test add time entry prompt with description."""
    result = prompts.get_add_time_entry_prompt(
        "ACME Corp", "Development", "2024-01-15", 2.5, "Fixed bug #123"
    )
    assert "ACME Corp" in result
    assert "Development" in result
    assert "2024-01-15" in result
    assert "2.5 hours" in result
    assert "Fixed bug #123" in result


def test_get_vacation_request_prompt():
    """Test vacation request prompt."""
    result = prompts.get_vacation_request_prompt("2024-07-01", "2024-07-14")
    assert "Request vacation" in result
    assert "2024-07-01" in result
    assert "2024-07-14" in result


def test_get_check_overtime_prompt():
    """Test check overtime prompt."""
    result = prompts.get_check_overtime_prompt(2024)
    assert "Check overtime compliance" in result
    assert "2024" in result
    assert "all employees" in result


def test_get_approve_vacation_prompt():
    """Test approve vacation prompt."""
    result = prompts.get_approve_vacation_prompt("John Doe", "2024-12-20 to 2024-12-31")
    assert "Approve vacation request" in result
    assert "John Doe" in result
    assert "2024-12-20 to 2024-12-31" in result
