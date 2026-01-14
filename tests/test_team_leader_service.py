# pylint: disable=redefined-outer-name
"""Tests for team leader service."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from clockodo_mcp.client import ClockodoClient
from clockodo_mcp.services.team_leader_service import TeamLeaderService


@pytest.fixture
def client():
    """Create a test client."""
    return ClockodoClient(
        api_user="test@example.com",
        api_key="test_key",
        base_url="https://my.clockodo.com/api/",
    )


@pytest.fixture
def service(client):
    """Create a test team leader service."""
    return TeamLeaderService(lambda: client)


@respx.mock
def test_approve_vacation(service, client):
    """Test approving a vacation request."""
    mock_response = {
        "absence": {
            "id": 123,
            "status": 1,
            "date_since": "2025-01-10",
            "date_until": "2025-01-15",
        }
    }

    respx.put(f"{client.base_url}v4/absences/123").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.approve_vacation(123)

    assert result == mock_response
    assert result["absence"]["status"] == 1


@respx.mock
def test_reject_vacation(service, client):
    """Test rejecting a vacation request."""
    mock_response = {
        "absence": {
            "id": 123,
            "status": 2,
            "date_since": "2025-01-10",
            "date_until": "2025-01-15",
        }
    }

    respx.put(f"{client.base_url}v4/absences/123").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.reject_vacation(123)

    assert result == mock_response
    assert result["absence"]["status"] == 2


@respx.mock
def test_list_pending_vacations(service, client):
    """Test listing pending vacation requests."""
    mock_response = {
        "absences": [
            {
                "id": 123,
                "status": 0,
                "type": 1,
                "date_since": "2025-01-10",
                "date_until": "2025-01-15",
                "users_id": 42,
            },
            {
                "id": 124,
                "status": 1,
                "type": 1,
                "date_since": "2025-02-01",
                "date_until": "2025-02-05",
                "users_id": 43,
            },
            {
                "id": 125,
                "status": 0,
                "type": 1,
                "date_since": "2025-03-01",
                "date_until": "2025-03-10",
                "users_id": 44,
            },
        ]
    }

    respx.get(f"{client.base_url}v4/absences").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.list_pending_vacations(2025)

    # Should only return status=0 (pending)
    assert len(result) == 2
    assert all(a["status"] == 0 for a in result)
    assert result[0]["id"] == 123
    assert result[1]["id"] == 125


@respx.mock
def test_edit_team_entry(service, client):
    """Test editing a team member's time entry."""
    mock_response = {
        "entry": {
            "id": 456,
            "time_since": "2025-01-15T10:00:00Z",
            "time_until": "2025-01-15T12:00:00Z",
            "text": "Updated description",
        }
    }

    respx.put(f"{client.base_url}v2/entries/456").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.edit_team_entry(456, {"text": "Updated description"})

    assert result == mock_response
    assert result["entry"]["text"] == "Updated description"


@respx.mock
def test_delete_team_entry(service, client):
    """Test deleting a team member's time entry."""
    mock_response = {"success": True}

    respx.delete(f"{client.base_url}v2/entries/456").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.delete_team_entry(456)

    assert result == mock_response


@respx.mock
def test_adjust_vacation_length(service, client):
    """Test adjusting vacation dates."""
    mock_response = {
        "absence": {
            "id": 123,
            "date_since": "2025-01-12",
            "date_until": "2025-01-14",
        }
    }

    respx.put(f"{client.base_url}v4/absences/123").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.adjust_vacation_length(123, "2025-01-12", "2025-01-14")

    assert result == mock_response
    assert result["absence"]["date_since"] == "2025-01-12"
    assert result["absence"]["date_until"] == "2025-01-14"


@respx.mock
def test_create_team_vacation_auto_approve(service, client):
    """Test creating a vacation for team member with auto-approval."""
    mock_response = {
        "absence": {
            "id": 789,
            "users_id": 42,
            "status": 1,
            "type": 1,
            "date_since": "2025-02-10",
            "date_until": "2025-02-15",
        }
    }

    respx.post(f"{client.base_url}v4/absences").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.create_team_vacation(
        user_id=42,
        date_since="2025-02-10",
        date_until="2025-02-15",
        auto_approve=True,
    )

    assert result == mock_response
    assert result["absence"]["status"] == 1  # approved


@respx.mock
def test_create_team_vacation_no_auto_approve(service, client):
    """Test creating a vacation for team member without auto-approval."""
    mock_response = {
        "absence": {
            "id": 789,
            "users_id": 42,
            "status": 0,
            "type": 1,
            "date_since": "2025-02-10",
            "date_until": "2025-02-15",
        }
    }

    respx.post(f"{client.base_url}v4/absences").mock(
        return_value=Response(200, json=mock_response)
    )

    result = service.create_team_vacation(
        user_id=42,
        date_since="2025-02-10",
        date_until="2025-02-15",
        auto_approve=False,
    )

    assert result == mock_response
    assert result["absence"]["status"] == 0  # enquired
