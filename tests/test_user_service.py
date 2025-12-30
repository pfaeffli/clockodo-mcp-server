import pytest
from unittest.mock import MagicMock
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
    client.get_clock.return_value = {
        "running": {"id": 1001},
        "stopped": None
    }

    service = UserService(client)
    service.stop_my_clock()

    # Should call get_clock and then clock_stop with the entry ID
    client.get_clock.assert_called_once()
    client.clock_stop.assert_called_once_with(1001)


def test_stop_my_clock_raises_when_not_running():
    client = MagicMock()
    # Mock get_clock to return no running clock
    client.get_clock.return_value = {
        "running": None,
        "stopped": None
    }

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
