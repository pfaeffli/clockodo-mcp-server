from unittest.mock import Mock, patch

from clockodo_mcp.server import (
    create_server,
    check_overtime_compliance,
    check_vacation_compliance,
    get_hr_summary,
)


def test_server_list_users_tool_calls_client():
    mock_client = Mock()
    mock_client.list_users.return_value = {"users": [{"id": 1}]}

    server = create_server(client=mock_client)

    # call the tool
    result = server.tools["list_users"]()

    mock_client.list_users.assert_called_once_with()
    assert result["users"][0]["id"] == 1


@patch("clockodo_mcp.server.ClockodoClient")
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


@patch("clockodo_mcp.server.ClockodoClient")
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


@patch("clockodo_mcp.server.ClockodoClient")
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
