from unittest.mock import MagicMock

import httpx
import pytest

from clockodo_mcp.services.user_service import UserService


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://example.test/")
    return httpx.HTTPStatusError(
        f"HTTP {status}",
        request=request,
        response=httpx.Response(status, request=request),
    )


def test_get_current_user_id():
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.get_me.return_value = {"data": {"id": 2, "email": "alice@example.com"}}

    service = UserService(client)

    assert service.get_current_user_id() == 2
    client.get_me.assert_called_once()
    client.list_users.assert_not_called()


def test_get_current_user_id_falls_back_to_email_scan_on_404():
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.get_me.side_effect = _status_error(404)
    client.list_users.return_value = {
        "users": [
            {"id": 1, "email": "bob@example.com"},
            {"id": 2, "email": "alice@example.com"},
        ]
    }

    assert UserService(client).get_current_user_id() == 2
    client.list_users.assert_called_once()


def test_get_current_user_id_does_not_swallow_other_errors():
    client = MagicMock()
    client.get_me.side_effect = _status_error(401)

    with pytest.raises(httpx.HTTPStatusError):
        UserService(client).get_current_user_id()
    client.list_users.assert_not_called()


def test_get_current_user_id_raises_when_not_found():
    client = MagicMock()
    client.api_user = "notfound@example.com"
    client.get_me.side_effect = _status_error(404)
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
    client.get_me.return_value = {"data": {"id": 2}}

    service = UserService(client)
    service.get_current_user_id()
    service.get_current_user_id()

    assert client.get_me.call_count == 1


def test_start_my_clock():
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 2, "email": "alice@example.com"}]
    }
    client.get_me.return_value = {"data": {"id": 2}}

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
    client = _own_absence_client()
    service = UserService(client)

    service.cancel_my_vacation(absence_id=2001)

    # Status 3 = approval cancelled (correct transition from status 1)
    client.edit_absence.assert_called_once_with(2001, {"status": 3})


def test_cancel_my_vacation_rejects_other_users_absence():
    client = _own_absence_client(users_id=99)
    service = UserService(client)

    with pytest.raises(PermissionError, match="Absence 2001 is not your absence"):
        service.cancel_my_vacation(absence_id=2001)

    client.edit_absence.assert_not_called()


def test_delete_my_vacation_without_auto_cancel():
    client = _own_absence_client()
    service = UserService(client)

    service.delete_my_vacation(absence_id=2001)

    client.delete_absence.assert_called_once_with(2001)


def test_delete_my_vacation_with_auto_cancel():
    client = _own_absence_client()
    service = UserService(client)

    service.delete_my_vacation(absence_id=2001, auto_cancel=True)

    # Should call edit_absence to cancel (status 3), then delete_absence
    client.edit_absence.assert_called_once_with(2001, {"status": 3})
    client.delete_absence.assert_called_once_with(2001)


@pytest.mark.parametrize("status", [400, 404, 409, 422])
def test_delete_my_vacation_auto_cancel_swallows_4xx(status):
    """A 4xx while cancelling (e.g. already cancelled) still allows deletion."""
    client = _own_absence_client()
    client.edit_absence.side_effect = _status_error(status)
    client.delete_absence.return_value = {"success": True}

    result = UserService(client).delete_my_vacation(absence_id=2001, auto_cancel=True)

    client.edit_absence.assert_called_once_with(2001, {"status": 3})
    client.delete_absence.assert_called_once_with(2001)
    assert result["success"] is True


@pytest.mark.parametrize(
    "error",
    [_status_error(429), _status_error(500), _status_error(503), RuntimeError("boom")],
)
def test_delete_my_vacation_auto_cancel_reraises_non_4xx(error):
    client = _own_absence_client()
    client.edit_absence.side_effect = error

    with pytest.raises(type(error)):
        UserService(client).delete_my_vacation(absence_id=2001, auto_cancel=True)

    client.delete_absence.assert_not_called()


def test_delete_my_vacation_auto_cancel_checks_ownership_once():
    client = _own_absence_client()

    UserService(client).delete_my_vacation(absence_id=2001, auto_cancel=True)

    client.get_absence.assert_called_once_with(2001)


@pytest.mark.parametrize("auto_cancel", [False, True])
def test_delete_my_vacation_rejects_other_users_absence(auto_cancel):
    client = _own_absence_client(users_id=99)
    service = UserService(client)

    with pytest.raises(PermissionError, match="Absence 2001 is not your absence"):
        service.delete_my_vacation(absence_id=2001, auto_cancel=auto_cancel)

    client.edit_absence.assert_not_called()
    client.delete_absence.assert_not_called()


def test_add_my_vacation():
    """Test adding vacation for current user."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.get_me.return_value = {"data": {"id": 42}}
    client.create_absence.return_value = {"absence": {"id": 2001}}

    service = UserService(client)
    result = service.add_my_vacation(date_since="2025-01-01", date_until="2025-01-05")

    client.create_absence.assert_called_once_with(
        date_since="2025-01-01",
        date_until="2025-01-05",
        absence_type=1,
        user_id=42,
        half_day=False,
    )
    assert result["absence"]["id"] == 2001


def test_add_my_vacation_half_day():
    """A single-day vacation can be booked as a half day."""
    client = _absence_client()

    service = UserService(client)
    service.add_my_vacation(
        date_since="2026-10-01", date_until="2026-10-01", half_day=True
    )

    client.create_absence.assert_called_once_with(
        date_since="2026-10-01",
        date_until="2026-10-01",
        absence_type=1,
        user_id=42,
        half_day=True,
    )


def test_add_my_vacation_half_day_rejects_multiple_days():
    """Clockodo only allows half-day absences on a single day."""
    client = _absence_client()

    service = UserService(client)
    with pytest.raises(ValueError, match="single day"):
        service.add_my_vacation(
            date_since="2026-09-28", date_until="2026-10-01", half_day=True
        )

    client.create_absence.assert_not_called()


def _own_absence_client(date_since="2026-09-28", date_until="2026-10-01", users_id=42):
    client = _absence_client()
    client.get_absence.return_value = {
        "data": {
            **_absence(2001),
            "users_id": users_id,
            "date_since": date_since,
            "date_until": date_until,
        }
    }
    return client


def test_edit_my_vacation_shortens_dates():
    """Only the given fields are sent to Clockodo."""
    client = _own_absence_client()
    client.edit_absence.return_value = {"data": {"id": 2001}}

    service = UserService(client)
    result = service.edit_my_vacation(2001, date_until="2026-09-30")

    client.get_absence.assert_called_once_with(2001)
    client.edit_absence.assert_called_once_with(2001, {"date_until": "2026-09-30"})
    assert result["data"]["id"] == 2001


def test_edit_my_vacation_sets_half_day():
    client = _own_absence_client(date_since="2026-10-01", date_until="2026-10-01")

    service = UserService(client)
    service.edit_my_vacation(2001, half_day=True)

    client.edit_absence.assert_called_once_with(2001, {"half_day": True})


def test_edit_my_vacation_half_day_rejects_multiple_days():
    """Half day on an absence that still spans several days is refused."""
    client = _own_absence_client(date_since="2026-09-28", date_until="2026-10-01")

    service = UserService(client)
    with pytest.raises(ValueError, match="single day"):
        service.edit_my_vacation(2001, half_day=True)

    client.edit_absence.assert_not_called()


def test_edit_my_vacation_keeps_stored_half_day_single_day():
    """Extending a stored half-day absence over several days is refused."""
    client = _own_absence_client(date_since="2026-10-05", date_until="2026-10-05")
    client.get_absence.return_value["data"]["half_day"] = True

    service = UserService(client)
    with pytest.raises(ValueError, match="single day"):
        service.edit_my_vacation(2001, date_until="2026-10-07")

    client.edit_absence.assert_not_called()


def test_edit_my_vacation_half_day_with_new_single_date():
    """New dates are checked, not the stored ones."""
    client = _own_absence_client(date_since="2026-09-28", date_until="2026-10-01")

    service = UserService(client)
    service.edit_my_vacation(
        2001, date_since="2026-10-01", date_until="2026-10-01", half_day=True
    )

    client.edit_absence.assert_called_once_with(
        2001,
        {"date_since": "2026-10-01", "date_until": "2026-10-01", "half_day": True},
    )


def test_edit_my_vacation_rejects_other_users_absence():
    """A team-leader key must not let the user tools edit a colleague's absence."""
    client = _own_absence_client(users_id=99)

    service = UserService(client)
    with pytest.raises(PermissionError, match="not your absence"):
        service.edit_my_vacation(2001, date_until="2026-09-30")

    client.edit_absence.assert_not_called()


def test_edit_my_vacation_requires_a_change():
    client = MagicMock()

    service = UserService(client)
    with pytest.raises(ValueError, match="Nothing to change"):
        service.edit_my_vacation(2001)

    client.edit_absence.assert_not_called()


def test_get_my_entries():
    """Test getting entries for current user."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.get_me.return_value = {"data": {"id": 42}}
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
    client.get_me.return_value = {"data": {"id": 42}}
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
    """Service layer should normalize space-separated dates to UTC (naive = Europe/Zurich)."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.get_me.return_value = {"data": {"id": 42}}
    client.list_entries.return_value = {"entries": []}

    service = UserService(client)
    service.get_my_entries(
        time_since="2025-01-01 00:00:00", time_until="2025-01-01 23:59:59"
    )

    client.list_entries.assert_called_once_with(
        time_since="2024-12-31T23:00:00Z",
        time_until="2025-01-01T22:59:59Z",
        user_id=42,
    )


def test_add_my_entry_normalizes_dates():
    """Service layer should normalize space-separated dates to UTC (naive = Europe/Zurich)."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.get_me.return_value = {"data": {"id": 42}}
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
        time_since="2025-01-01T08:00:00Z",
        time_until="2025-01-01T09:00:00Z",
        projects_id=None,
        text=None,
        user_id=42,
    )


def test_add_my_entry_with_text():
    """Test that text parameter is passed through to the client."""
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.get_me.return_value = {"data": {"id": 42}}
    client.create_entry.return_value = {
        "entry": {"id": 3001, "text": "Work description", "texts_id": 555}
    }

    service = UserService(client)
    result = service.add_my_entry(
        customers_id=123,
        services_id=456,
        billable=0,
        time_since="2025-01-01T09:00:00Z",
        time_until="2025-01-01T10:00:00Z",
        text="Work description",
    )

    client.create_entry.assert_called_once_with(
        customers_id=123,
        services_id=456,
        billable=0,
        time_since="2025-01-01T09:00:00Z",
        time_until="2025-01-01T10:00:00Z",
        projects_id=None,
        text="Work description",
        user_id=42,
    )
    assert result["entry"]["text"] == "Work description"


def _own_entry_client(users_id=42):
    client = _absence_client()
    client.get_entry.return_value = {"entry": {"id": 3001, "users_id": users_id}}
    return client


def test_edit_my_entry():
    """Only passed fields reach the API; times are normalised to UTC."""
    client = _own_entry_client()
    client.edit_entry.return_value = {"entry": {"id": 3001, "text": "Updated"}}

    service = UserService(client)
    result = service.edit_my_entry(
        entry_id=3001,
        time_since="2025-01-01T10:00:00+01:00",
        time_until="2025-01-01T11:00:00Z",
        text="Updated",
        customers_id=1,
        services_id=2,
        projects_id=3,
        billable=0,
    )

    client.edit_entry.assert_called_once_with(
        3001,
        {
            "time_since": "2025-01-01T09:00:00Z",
            "time_until": "2025-01-01T11:00:00Z",
            "text": "Updated",
            "customers_id": 1,
            "services_id": 2,
            "projects_id": 3,
            "billable": 0,
        },
    )
    assert result["entry"]["text"] == "Updated"


def test_edit_my_entry_sends_only_passed_params():
    client = _own_entry_client()

    UserService(client).edit_my_entry(entry_id=3001, billable=0, text="")

    client.edit_entry.assert_called_once_with(3001, {"text": "", "billable": 0})


def test_edit_my_entry_requires_a_change():
    client = _own_entry_client()

    with pytest.raises(ValueError, match="at least one"):
        UserService(client).edit_my_entry(entry_id=3001)

    client.edit_entry.assert_not_called()


def test_edit_my_entry_rejects_invalid_billable():
    client = _own_entry_client()

    with pytest.raises(ValueError, match="billable"):
        UserService(client).edit_my_entry(entry_id=3001, billable=5)

    client.edit_entry.assert_not_called()


def test_edit_my_entry_rejects_other_users_entry():
    client = _own_entry_client(users_id=99)

    service = UserService(client)
    with pytest.raises(PermissionError, match="Entry 3001 is not your entry"):
        service.edit_my_entry(entry_id=3001, text="Updated")

    client.edit_entry.assert_not_called()


def test_edit_my_entry_cannot_take_users_id():
    """Reassigning an entry is impossible: users_id is not a parameter."""
    client = _own_entry_client()

    with pytest.raises(TypeError):
        UserService(client).edit_my_entry(  # type: ignore[call-arg]  # pylint: disable=unexpected-keyword-arg
            entry_id=3001, users_id=99
        )

    client.edit_entry.assert_not_called()


def test_delete_my_entry():
    """Test deleting an entry."""
    client = _own_entry_client()
    client.delete_entry.return_value = {"success": True}

    service = UserService(client)
    result = service.delete_my_entry(entry_id=3001)

    client.delete_entry.assert_called_once_with(3001)
    assert result["success"] is True


def test_delete_my_entry_rejects_other_users_entry():
    client = _own_entry_client(users_id=99)

    service = UserService(client)
    with pytest.raises(PermissionError, match="Entry 3001 is not your entry"):
        service.delete_my_entry(entry_id=3001)

    client.delete_entry.assert_not_called()


def _absence(absence_id, abs_type=1):
    return {
        "id": absence_id,
        "users_id": 42,
        "date_since": "2025-07-01",
        "date_until": "2025-07-05",
        "type": abs_type,
        "status": 1,
        "count_days": 5,
        "note": "Summer holiday",
    }


def _absence_client():
    client = MagicMock()
    client.api_user = "alice@example.com"
    client.list_users.return_value = {
        "users": [{"id": 42, "email": "alice@example.com"}]
    }
    client.get_me.return_value = {"data": {"id": 42}}
    return client


def test_get_my_absences_requests_current_user_only():
    """The API is asked for the authenticated user's absences only."""
    client = _absence_client()
    client.list_absences.return_value = {"absences": [_absence(2001)]}

    service = UserService(client)
    result = service.get_my_absences(year=2025)

    client.list_absences.assert_called_once_with(2025, user_id=42, absence_type=None)
    assert [a["id"] for a in result["absences"]] == [2001]


def test_get_my_absences_filters_by_type():
    """Optional absence_type is passed through to the API filter."""
    client = _absence_client()
    client.list_absences.return_value = {"absences": [_absence(2002, abs_type=2)]}

    service = UserService(client)
    result = service.get_my_absences(year=2025, absence_type=2)

    client.list_absences.assert_called_once_with(2025, user_id=42, absence_type=2)
    assert [a["id"] for a in result["absences"]] == [2002]


def test_get_my_absences_handles_missing_absences_key():
    """A response without absences yields an empty list, not an error."""
    client = _absence_client()
    client.list_absences.return_value = {}

    service = UserService(client)
    result = service.get_my_absences(year=2025)

    assert result["absences"] == []


def test_add_my_sick_day():
    client = _absence_client()

    UserService(client).add_my_sick_day(
        date_since="2026-10-01", date_until="2026-10-02"
    )

    client.create_absence.assert_called_once_with(
        date_since="2026-10-01",
        date_until="2026-10-02",
        absence_type=4,
        user_id=42,
        sick_note=False,
    )


def test_add_my_sick_day_child_with_note():
    client = _absence_client()

    UserService(client).add_my_sick_day(
        date_since="2026-10-01", date_until="2026-10-01", sick_note=True, child=True
    )

    client.create_absence.assert_called_once_with(
        date_since="2026-10-01",
        date_until="2026-10-01",
        absence_type=5,
        user_id=42,
        sick_note=True,
    )
