"""
Tests for MCP prompts and resources registration in server.py.
"""

# pylint: disable=redefined-outer-name  # pytest fixtures

from unittest.mock import MagicMock, patch

import pytest

# Import the mcp object and functions directly
from clockodo_mcp import server


def test_start_tracking_prompt():
    """Test start_tracking prompt."""
    result = server.start_tracking("ACME Corp", "Development", "Website")
    assert "ACME Corp" in result
    assert "Development" in result
    assert "Website" in result


def test_start_tracking_prompt_no_project():
    """Test start_tracking prompt without project."""
    result = server.start_tracking("ACME Corp", "Development")
    assert "ACME Corp" in result
    assert "Development" in result


def test_stop_tracking_prompt():
    """Test stop_tracking prompt."""
    result = server.stop_tracking()
    assert "Stop tracking time" in result


def test_request_vacation_prompt():
    """Test request_vacation prompt."""
    result = server.request_vacation("2024-07-01", "2024-07-14")
    assert "2024-07-01" in result
    assert "2024-07-14" in result
    assert "vacation" in result.lower()


@pytest.fixture
def mock_client():
    """Create a mock ClockodoClient."""
    client = MagicMock()
    return client


def test_current_entry_resource_no_clock(mock_client):
    """Test current_entry resource when no clock is running."""
    mock_client.get_clock.return_value = {}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = server.current_entry()

    # Should return JSON string
    assert isinstance(result, str)
    assert "running" in result
    assert "false" in result.lower()


def test_current_entry_resource_with_clock(mock_client):
    """Test current_entry resource with running clock."""
    mock_client.get_clock.return_value = {
        "running": {
            "id": 123,
            "customers_name": "ACME Corp",
            "services_name": "Development",
        }
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = server.current_entry()

    assert isinstance(result, str)
    assert "123" in result
    assert "ACME Corp" in result
    assert "Development" in result


def test_customers_list_resource(mock_client):
    """Test customers_list resource."""
    mock_client.list_customers.return_value = {
        "customers": [
            {"id": 1, "name": "ACME Corp"},
            {"id": 2, "name": "TechStart Inc"},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = server.customers_list()

    assert isinstance(result, str)
    assert "ACME Corp" in result
    assert "TechStart Inc" in result
    assert '"count": 2' in result


def test_services_list_resource(mock_client):
    """Test services_list resource."""
    mock_client.list_services.return_value = {
        "services": [
            {"id": 1, "name": "Development"},
            {"id": 2, "name": "Design"},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = server.services_list()

    assert isinstance(result, str)
    assert "Development" in result
    assert "Design" in result
    assert '"count": 2' in result


def test_recent_entries_resource(mock_client):
    """Test recent_entries resource."""
    mock_client.list_entries.return_value = {
        "entries": [
            {"id": 1, "customers_name": "ACME Corp", "duration": 3600},
            {"id": 2, "customers_name": "TechStart Inc", "duration": 7200},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = server.recent_entries()

    assert isinstance(result, str)
    assert "ACME Corp" in result
    assert "TechStart Inc" in result
    assert '"count": 2' in result
    assert "period" in result


def test_recent_entries_resource_empty(mock_client):
    """Test recent_entries resource with no entries."""
    mock_client.list_entries.return_value = {"entries": []}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = server.recent_entries()

    assert isinstance(result, str)
    assert '"count": 0' in result
