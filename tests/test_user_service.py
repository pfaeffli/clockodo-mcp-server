from unittest.mock import MagicMock

import pytest

from clockodo_mcp.services.user_service import UserService


def test_get_current_user_id():
    client = MagicMock()
    # Mock list_users to return a list where one user matches the client's api_user
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [
            {"id": 1, "email": "bob@example.com"},
            {"id": 2, "email": "alice@example.com"},
        ]
    }

    service = UserService(client)
    user_id = service.get_current_user_id()

    assert user_id == 2
    client.list_users.assert_called_once()


def test_get_current_user_id_raises_when_not_found():
    client = MagicMock()
    client.api_user = "notfound@example.com"
    client.list_users.return_value = {
        "users": [
            {"id": 1, "email": "bob@example.com"},
            {"id": 2, "email": "alice@example.com"},
        ]
    }

    service = UserService(client)

    with pytest.raises(ValueError, match="Could not find user with email"):
        service.get_current_user_id()


def test_get_my_clock():
    client = MagicMock()
    client.get_clock.return_value = {"running": None, "stopped": None}

    service = UserService(client)
    result = service.get_my_clock()

    client.get_clock.assert_called_once()
    assert result["running"] is None


def test_get_current_user_id_cached():
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 2, "email": "alice@example.com"}]
    }

    service = UserService(client)
    service.get_current_user_id()
    service.get_current_user_id()

    assert client.list_users.call_count == 1


def test_start_my_clock():
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 2, "email": "alice@example.com"}]
    }

    service = UserService(client)
    service.start_my_clock(customers_id=123, services_id=456)

    # billable is now optional (None by default)
    client.clock_start.assert_called_once_with(
        customers_id=123, services_id=456, billable=None, projects_id=None, text=None
    )


def test_stop_my_clock():
    client = MagicMock()
    # Mock get_clock to return a running clock with ID
    client.get_clock.return_value = {"running": {"id": 1001}, "stopped": None}

    service = UserService(client)
    service.stop_my_clock()

    # Should call get_clock and then clock_stop with the entry ID
    client.get_clock.assert_called_once()
    client.clock_stop.assert_called_once_with(1001)


def test_stop_my_clock_raises_when_not_running():
    client = MagicMock()
    # Mock get_clock to return no running clock
    client.get_clock.return_value = {"running": None, "stopped": None}

    service = UserService(client)

    with pytest.raises(ValueError, match="No clock is currently running"):
        service.stop_my_clock()


def test_cancel_my_vacation():
    client = MagicMock()
    service = UserService(client)

    service.cancel_my_vacation(absence_id=2001)

    # Status 3 = approval cancelled (correct transition from status 1)
    client.edit_absence.assert_called_once_with(2001, {"status": 3})


def test_delete_my_vacation_without_auto_cancel():
    client = MagicMock()
    service = UserService(client)

    service.delete_my_vacation(absence_id=2001)

    client.delete_absence.assert_called_once_with(2001)


def test_delete_my_vacation_with_auto_cancel():
    client = MagicMock()
    service = UserService(client)

    service.delete_my_vacation(absence_id=2001, auto_cancel=True)

    # Should call edit_absence to cancel (status 3), then delete_absence
    client.edit_absence.assert_called_once_with(2001, {"status": 3})
    client.delete_absence.assert_called_once_with(2001)


def test_delete_my_vacation_with_auto_cancel_failure():
    """Test delete_my_vacation when cancel fails but deletion continues."""
    client = MagicMock()
    client.edit_absence.side_effect = Exception("Cancel failed")
    client.delete_absence.return_value = {"success": True}

    service = UserService(client)

    # Should still attempt deletion even if cancel fails
    result = service.delete_my_vacation(absence_id=2001, auto_cancel=True)

    client.edit_absence.assert_called_once_with(2001, {"status": 3})
    client.delete_absence.assert_called_once_with(2001)
    assert result["success"] is True


def test_add_my_vacation():
    """Test adding vacation for current user."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.create_absence.return_value = {"absence": {"id": 2001}}

    service = UserService(client)
    result = service.add_my_vacation(date_since="2025-01-01", date_until="2025-01-05")

    client.create_absence.assert_called_once_with(
        date_since="2025-01-01", date_until="2025-01-05", absence_type=1, user_id=42
    )
    assert result["absence"]["id"] == 2001


def test_get_my_entries():
    """Test getting entries for current user."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.list_entries.return_value = {"entries": [{"id": 3001}]}

    service = UserService(client)
    result = service.get_my_entries(
        time_since="2025-01-01T00:00:00Z", time_until="2025-01-01T23:59:59Z"
    )

    client.list_entries.assert_called_once_with(
        time_since="2025-01-01T00:00:00Z", time_until="2025-01-01T23:59:59Z", user_id=42
    )
    assert result["entries"][0]["id"] == 3001


def test_add_my_entry():
    """Test adding entry for current user."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.create_entry.return_value = {"entry": {"id": 3001}}

    service = UserService(client)
    result = service.add_my_entry(
        customers_id=123,
        services_id=456,
        billable=1,
        time_since="2025-01-01T09:00:00Z",
        time_until="2025-01-01T10:00:00Z",
    )

    client.create_entry.assert_called_once_with(
        customers_id=123,
        services_id=456,
        billable=1,
        time_since="2025-01-01T09:00:00Z",
        time_until="2025-01-01T10:00:00Z",
        projects_id=None,
        text=None,
        user_id=42,
    )
    assert result["entry"]["id"] == 3001


def test_get_my_entries_normalizes_dates():
    """Service layer should normalize space-separated dates to ISO 8601."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.list_entries.return_value = {"entries": []}

    service = UserService(client)
    service.get_my_entries(
        time_since="2025-01-01 00:00:00", time_until="2025-01-01 23:59:59"
    )

    client.list_entries.assert_called_once_with(
        time_since="2025-01-01T00:00:00Z",
        time_until="2025-01-01T23:59:59Z",
        user_id=42,
    )


def test_add_my_entry_normalizes_dates():
    """Service layer should normalize space-separated dates to ISO 8601."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.create_entry.return_value = {"entry": {"id": 3001}}

    service = UserService(client)
    service.add_my_entry(
        customers_id=123,
        services_id=456,
        billable=1,
        time_since="2025-01-01 09:00:00",
        time_until="2025-01-01 10:00:00",
    )

    client.create_entry.assert_called_once_with(
        customers_id=123,
        services_id=456,
        billable=1,
        time_since="2025-01-01T09:00:00Z",
        time_until="2025-01-01T10:00:00Z",
        projects_id=None,
        text=None,
        user_id=42,
    )


def test_edit_my_entry():
    """Test editing an entry."""
    client = MagicMock()
    client.edit_entry.return_value = {"entry": {"id": 3001, "text": "Updated"}}

    service = UserService(client)
    result = service.edit_my_entry(entry_id=3001, data={"text": "Updated"})

    client.edit_entry.assert_called_once_with(3001, {"text": "Updated"})
    assert result["entry"]["text"] == "Updated"


def test_delete_my_entry():
    """Test deleting an entry."""
    client = MagicMock()
    client.delete_entry.return_value = {"success": True}

    service = UserService(client)
    result = service.delete_my_entry(entry_id=3001)

    client.delete_entry.assert_called_once_with(3001)
    assert result["success"] is True
