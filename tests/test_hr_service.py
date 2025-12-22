from unittest.mock import Mock

from clockodo_mcp.services.hr_service import HRService


def test_hr_service_check_overtime_compliance():
    mock_client = Mock()
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

    service = HRService(mock_client)
    result = service.check_overtime_compliance(year=2024, max_overtime_hours=80)

    mock_client.get_user_reports.assert_called_once_with(year=2024)
    assert result["year"] == 2024
    assert result["threshold"] == 80
    assert len(result["violations"]) == 1
    assert result["violations"][0]["user_name"] == "Alice"
    assert result["violations"][0]["overtime_hours"] == 100.0


def test_hr_service_check_vacation_compliance():
    mock_client = Mock()
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

    service = HRService(mock_client)
    result = service.check_vacation_compliance(year=2024, min_vacation_days=10)

    mock_client.get_user_reports.assert_called_once_with(year=2024)
    assert result["year"] == 2024
    assert result["min_vacation_days"] == 10
    assert len(result["violations"]) == 1
    assert result["violations"][0]["user_name"] == "Bob"


def test_hr_service_get_hr_summary():
    mock_client = Mock()
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

    service = HRService(mock_client)
    result = service.get_hr_summary(year=2024)

    mock_client.get_user_reports.assert_called_once_with(year=2024)
    assert result["year"] == 2024
    assert result["total_employees"] == 2
    assert len(result["employees_with_violations"]) == 1
    assert result["employees_with_violations"][0]["user_name"] == "Alice"
    assert len(result["employees_with_violations"][0]["violations"]) == 2
