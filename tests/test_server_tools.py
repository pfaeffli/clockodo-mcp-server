from unittest.mock import Mock, patch

from clockodo_mcp.server import create_server
from clockodo_mcp.tools.hr_tools import (
    check_overtime_compliance,
    check_vacation_compliance,
    get_hr_summary,
)
from clockodo_mcp.tools.user_tools import (
    get_my_clock,
    start_my_clock,
    stop_my_clock,
    add_my_vacation,
    get_my_entries,
    add_my_entry,
    edit_my_entry,
    delete_my_entry,
    delete_my_vacation,
)
from clockodo_mcp.tools.debug_tools import get_raw_user_reports


def test_server_list_users_tool_calls_client():
    mock_client = Mock()
    mock_client.list_users.return_value = {"users": [{"id": 1}]}

    server = create_server(client=mock_client)

    # call the tool
    result = server.tools["list_users"]()

    mock_client.list_users.assert_called_once_with()
    assert result["users"][0]["id"] == 1


def test_server_list_customers_tool_calls_client():
    mock_client = Mock()
    mock_client.list_customers.return_value = {"customers": [{"id": 100}]}

    server = create_server(client=mock_client)

    # call the tool
    result = server.tools["list_customers"]()

    mock_client.list_customers.assert_called_once_with()
    assert result["customers"][0]["id"] == 100


def test_server_list_services_tool_calls_client():
    mock_client = Mock()
    mock_client.list_services.return_value = {"services": [{"id": 200}]}

    server = create_server(client=mock_client)

    # call the tool
    result = server.tools["list_services"]()

    mock_client.list_services.assert_called_once_with()
    assert result["services"][0]["id"] == 200


@patch("clockodo_mcp.tools.hr_tools.ClockodoClient")
def test_check_overtime_compliance_returns_violations(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.get_user_reports.return_value = {
        "userreports": [
            {
                "users_id": 1,
                "users_name": "Alice",
                "year": 2024,
                "diff": 360000,  # 100 hours
                "overtime_carryover": 0,
                "holidays_quota": 25,
                "holidays_carry": 0,
            }
        ]
    }

    result = check_overtime_compliance(year=2024, max_overtime_hours=80)

    mock_client.get_user_reports.assert_called_once_with(year=2024)
    assert result["year"] == 2024
    assert result["threshold"] == 80
    assert len(result["violations"]) == 1
    assert result["violations"][0]["user_name"] == "Alice"
    assert result["violations"][0]["overtime_hours"] == 100.0


@patch("clockodo_mcp.tools.hr_tools.ClockodoClient")
def test_check_vacation_compliance_returns_violations(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.get_user_reports.return_value = {
        "userreports": [
            {
                "users_id": 1,
                "users_name": "Bob",
                "year": 2024,
                "diff": 0,
                "overtime_carryover": 0,
                "holidays_quota": 20,
                "holidays_carry": 0,
                "sum_absence": {"regular_holidays": 3.0},
            }
        ]
    }

    result = check_vacation_compliance(year=2024, min_vacation_days=10)

    mock_client.get_user_reports.assert_called_once_with(year=2024)
    assert result["year"] == 2024
    assert result["min_vacation_days"] == 10
    assert len(result["violations"]) == 1
    assert result["violations"][0]["user_name"] == "Bob"


@patch("clockodo_mcp.tools.hr_tools.ClockodoClient")
def test_get_hr_summary_returns_complete_report(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.get_user_reports.return_value = {
        "userreports": [
            {
                "users_id": 1,
                "users_name": "Alice",
                "year": 2024,
                "diff": 360000,  # 100 hours
                "overtime_carryover": 0,
                "holidays_quota": 20,
                "holidays_carry": 0,
                "sum_absence": {"regular_holidays": 5.0},
            },
            {
                "users_id": 2,
                "users_name": "Bob",
                "year": 2024,
                "diff": 36000,  # 10 hours
                "overtime_carryover": 0,
                "holidays_quota": 25,
                "holidays_carry": 0,
                "sum_absence": {"regular_holidays": 15.0},
            },
        ]
    }

    result = get_hr_summary(year=2024)

    mock_client.get_user_reports.assert_called_once_with(year=2024)
    assert result["year"] == 2024
    assert result["total_employees"] == 2
    assert len(result["employees_with_violations"]) == 1
    assert result["employees_with_violations"][0]["user_name"] == "Alice"
    assert len(result["employees_with_violations"][0]["violations"]) == 2


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_start_my_clock_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.clock_start.return_value = {"running": {"id": 100}}

    result = start_my_clock(customers_id=1, services_id=2)

    mock_client.clock_start.assert_called_once_with(
        customers_id=1, services_id=2, billable=1, projects_id=None, text=None
    )
    assert result["running"]["id"] == 100


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_stop_my_clock_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    # Mock get_clock to return a running clock with ID
    mock_client.get_clock.return_value = {"running": {"id": 1001}, "stopped": None}
    mock_client.clock_stop.return_value = {"stopped": {"id": 1001}, "running": None}

    result = stop_my_clock()

    mock_client.get_clock.assert_called_once()
    mock_client.clock_stop.assert_called_once_with(1001)
    assert result["stopped"]["id"] == 1001


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_add_my_vacation_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.api_user = "me@example.com"
    mock_client.list_users.return_value = {
        "users": [{"id": 42, "email": "me@example.com"}]
    }
    mock_client.create_absence.return_value = {"absence": {"id": 200}}

    result = add_my_vacation(date_since="2025-01-01", date_until="2025-01-05")

    mock_client.create_absence.assert_called_once_with(
        date_since="2025-01-01", date_until="2025-01-05", absence_type=1, user_id=42
    )
    assert result["absence"]["id"] == 200


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_get_my_clock_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.get_clock.return_value = {"running": None, "stopped": None}

    result = get_my_clock()

    mock_client.get_clock.assert_called_once()
    assert result["running"] is None


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_get_my_entries_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.api_user = "me@example.com"
    mock_client.list_users.return_value = {
        "users": [{"id": 42, "email": "me@example.com"}]
    }
    mock_client.list_entries.return_value = {"entries": [{"id": 100}]}

    result = get_my_entries(
        time_since="2025-01-01T00:00:00Z", time_until="2025-01-01T23:59:59Z"
    )

    mock_client.list_entries.assert_called_once()
    assert result["entries"][0]["id"] == 100


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_add_my_entry_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.api_user = "me@example.com"
    mock_client.list_users.return_value = {
        "users": [{"id": 42, "email": "me@example.com"}]
    }
    mock_client.create_entry.return_value = {"entry": {"id": 300}}

    result = add_my_entry(
        customers_id=123,
        services_id=456,
        time_since="2025-01-01T09:00:00Z",
        time_until="2025-01-01T10:00:00Z",
        billable=1,
    )

    mock_client.create_entry.assert_called_once()
    assert result["entry"]["id"] == 300


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_edit_my_entry_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.edit_entry.return_value = {"entry": {"id": 300, "text": "Updated"}}

    result = edit_my_entry(entry_id=300, data={"text": "Updated"})

    mock_client.edit_entry.assert_called_once_with(300, {"text": "Updated"})
    assert result["entry"]["text"] == "Updated"


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_delete_my_entry_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.delete_entry.return_value = {"success": True}

    result = delete_my_entry(entry_id=300)

    mock_client.delete_entry.assert_called_once_with(300)
    assert result["success"] is True


@patch("clockodo_mcp.tools.user_tools.ClockodoClient")
def test_delete_my_vacation_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.delete_absence.return_value = {"success": True}

    result = delete_my_vacation(absence_id=200)

    mock_client.delete_absence.assert_called_once_with(200)
    assert result["success"] is True


@patch("clockodo_mcp.tools.debug_tools.ClockodoClient")
def test_get_raw_user_reports_tool(mock_client_class):
    mock_client = Mock()
    mock_client_class.from_env.return_value = mock_client
    mock_client.get_user_reports.return_value = {
        "userreports": [{"users_id": 1, "sum_hours": 144000}]
    }

    result = get_raw_user_reports(year=2025)

    mock_client.get_user_reports.assert_called_once_with(year=2025)
    assert result["userreports"][0]["users_id"] == 1
