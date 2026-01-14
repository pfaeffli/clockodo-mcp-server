"""
Tests for resources.py module.
"""

# pylint: disable=redefined-outer-name  # pytest fixtures

from unittest.mock import MagicMock, patch

import pytest

from clockodo_mcp import resources


@pytest.fixture
def mock_client():
    """Create a mock ClockodoClient."""
    client = MagicMock()
    return client


def test_get_current_time_entry_resource_no_running_clock(mock_client):
    """Test current time entry resource when no clock is running."""
    mock_client.get_clock.return_value = {}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_current_time_entry_resource()

    assert result["uri"] == "clockodo://current-entry"
    assert result["name"] == "Current Time Entry"
    assert "No time entry" in result["description"]
    assert result["mimeType"] == "application/json"
    assert result["content"]["running"] is False


def test_get_current_time_entry_resource_with_running_clock(mock_client):
    """Test current time entry resource when a clock is running."""
    mock_client.get_clock.return_value = {
        "running": {
            "id": 123,
            "customers_name": "ACME Corp",
            "services_name": "Development",
            "text": "Working on feature",
        }
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_current_time_entry_resource()

    assert result["uri"] == "clockodo://current-entry"
    assert result["name"] == "Current Time Entry"
    assert "ACME Corp" in result["description"]
    assert "Development" in result["description"]
    assert result["content"]["id"] == 123
    assert result["content"]["customers_name"] == "ACME Corp"


def test_get_user_profile_resource(mock_client):
    """Test user profile resource."""
    mock_client.list_users.return_value = {
        "users": [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "Jane Smith"},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_user_profile_resource()

    assert result["uri"] == "clockodo://user-profile"
    assert result["name"] == "User Profile"
    assert result["mimeType"] == "application/json"
    assert result["content"]["users_count"] == 2


def test_get_customers_resource(mock_client):
    """Test customers resource."""
    mock_client.list_customers.return_value = {
        "customers": [
            {"id": 1, "name": "ACME Corp"},
            {"id": 2, "name": "TechStart Inc"},
            {"id": 3, "name": "Global Solutions"},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_customers_resource()

    assert result["uri"] == "clockodo://customers"
    assert result["name"] == "Customers List"
    assert "3 total" in result["description"]
    assert result["content"]["count"] == 3
    assert "ACME Corp" in result["content"]["names"]
    assert "TechStart Inc" in result["content"]["names"]
    assert len(result["content"]["customers"]) == 3


def test_get_customers_resource_empty(mock_client):
    """Test customers resource with no customers."""
    mock_client.list_customers.return_value = {"customers": []}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_customers_resource()

    assert result["content"]["count"] == 0
    assert result["content"]["customers"] == []
    assert result["content"]["names"] == []


def test_get_services_resource(mock_client):
    """Test services resource."""
    mock_client.list_services.return_value = {
        "services": [
            {"id": 1, "name": "Development"},
            {"id": 2, "name": "Design"},
            {"id": 3, "name": "Consulting"},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_services_resource()

    assert result["uri"] == "clockodo://services"
    assert result["name"] == "Services List"
    assert "3 total" in result["description"]
    assert result["content"]["count"] == 3
    assert "Development" in result["content"]["names"]
    assert "Design" in result["content"]["names"]
    assert len(result["content"]["services"]) == 3


def test_get_services_resource_empty(mock_client):
    """Test services resource with no services."""
    mock_client.list_services.return_value = {"services": []}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_services_resource()

    assert result["content"]["count"] == 0
    assert result["content"]["services"] == []
    assert result["content"]["names"] == []


def test_get_projects_resource(mock_client):
    """Test projects resource."""
    mock_client.list_projects.return_value = {
        "projects": [
            {"id": 1, "name": "Project Alpha"},
            {"id": 2, "name": "Project Beta"},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_projects_resource()

    assert result["uri"] == "clockodo://projects"
    assert result["name"] == "Projects List"
    assert "2 total" in result["description"]
    assert result["content"]["count"] == 2
    assert "Project Alpha" in result["content"]["names"]
    assert "Project Beta" in result["content"]["names"]
    assert len(result["content"]["projects"]) == 2


def test_get_projects_resource_empty(mock_client):
    """Test projects resource with no projects."""
    mock_client.list_projects.return_value = {"projects": []}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_projects_resource()

    assert result["content"]["count"] == 0
    assert result["content"]["projects"] == []
    assert result["content"]["names"] == []


def test_get_recent_entries_resource(mock_client):
    """Test recent entries resource."""
    mock_client.list_entries.return_value = {
        "entries": [
            {"id": 1, "customers_name": "ACME Corp", "duration": 3600},
            {"id": 2, "customers_name": "TechStart Inc", "duration": 7200},
            {"id": 3, "customers_name": "ACME Corp", "duration": 5400},
        ]
    }

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_recent_entries_resource(days=7)

    assert "clockodo://recent-entries?days=7" in result["uri"]
    assert "Last 7 Days" in result["name"]
    assert "3 entries" in result["description"]
    assert result["content"]["count"] == 3
    assert len(result["content"]["entries"]) == 3
    assert "period" in result["content"]
    assert "start" in result["content"]["period"]
    assert "end" in result["content"]["period"]

    # Verify client was called with correct date range
    mock_client.list_entries.assert_called_once()
    call_kwargs = mock_client.list_entries.call_args[1]
    assert "time_since" in call_kwargs
    assert "time_until" in call_kwargs


def test_get_recent_entries_resource_custom_days(mock_client):
    """Test recent entries resource with custom days parameter."""
    mock_client.list_entries.return_value = {"entries": []}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_recent_entries_resource(days=14)

    assert "clockodo://recent-entries?days=14" in result["uri"]
    assert "Last 14 Days" in result["name"]
    assert result["content"]["count"] == 0


def test_get_recent_entries_resource_empty(mock_client):
    """Test recent entries resource with no entries."""
    mock_client.list_entries.return_value = {"entries": []}

    with patch(
        "clockodo_mcp.resources.ClockodoClient.from_env", return_value=mock_client
    ):
        result = resources.get_recent_entries_resource(days=7)

    assert result["content"]["count"] == 0
    assert result["content"]["entries"] == []
