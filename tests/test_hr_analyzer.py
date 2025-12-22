from clockodo_mcp.hr_analyzer import analyze_overtime, analyze_vacation, get_hr_violations


def test_analyze_overtime_no_violation_when_under_threshold():
    report = {
        "users_id": 1,
        "users_name": "Alice",
        "year": 2024,
        "diff": 72000,  # 20 hours in seconds
        "overtime_carryover": 0,
    }

    result = analyze_overtime(report, max_hours_threshold=80)

    assert result["has_violation"] is False
    assert result["overtime_hours"] == 20.0
    assert result["threshold"] == 80


def test_analyze_overtime_violation_when_exceeds_threshold():
    report = {
        "users_id": 2,
        "users_name": "Bob",
        "year": 2024,
        "diff": 288000,  # 80 hours in seconds
        "overtime_carryover": 18000,  # 5 hours in seconds
    }

    result = analyze_overtime(report, max_hours_threshold=80)

    assert result["has_violation"] is True
    assert result["overtime_hours"] == 85.0
    assert result["excess_hours"] == 5.0


def test_analyze_overtime_with_negative_diff():
    report = {
        "users_id": 3,
        "users_name": "Charlie",
        "year": 2024,
        "diff": -36000,  # -10 hours in seconds
        "overtime_carryover": 0,
    }

    result = analyze_overtime(report, max_hours_threshold=80)

    assert result["has_violation"] is False
    assert result["overtime_hours"] == -10.0


def test_analyze_vacation_no_violation_when_within_range():
    report = {
        "users_id": 1,
        "users_name": "Alice",
        "year": 2024,
        "holidays_quota": 25,
        "holidays_carry": 2.5,
        "sum_absence": {
            "regular_holidays": 15.0,
        }
    }

    result = analyze_vacation(report, min_days_used=10, max_days_remaining=15)

    assert result["has_violation"] is False
    assert result["used_days"] == 15.0
    assert result["remaining_days"] == 12.5


def test_analyze_vacation_violation_when_too_few_used():
    report = {
        "users_id": 2,
        "users_name": "Bob",
        "year": 2024,
        "holidays_quota": 20,
        "holidays_carry": 0,
        "sum_absence": {
            "regular_holidays": 5.0,
        }
    }

    result = analyze_vacation(report, min_days_used=10, max_days_remaining=20)

    assert result["has_violation"] is True
    assert result["violation_type"] == "insufficient_vacation_taken"
    assert result["used_days"] == 5.0
    assert result["days_short"] == 5.0


def test_analyze_vacation_violation_when_too_many_remaining():
    report = {
        "users_id": 3,
        "users_name": "Charlie",
        "year": 2024,
        "holidays_quota": 25,
        "holidays_carry": 5,
        "sum_absence": {
            "regular_holidays": 8.0,
        }
    }

    result = analyze_vacation(report, min_days_used=10, max_days_remaining=15)

    assert result["has_violation"] is True
    assert result["violation_type"] == "excessive_vacation_remaining"
    assert result["remaining_days"] == 22.0
    assert result["excess_days"] == 7.0


def test_analyze_vacation_handles_missing_sum_absence():
    report = {
        "users_id": 4,
        "users_name": "Diana",
        "year": 2024,
        "holidays_quota": 25,
        "holidays_carry": 0,
    }

    result = analyze_vacation(report, min_days_used=10, max_days_remaining=15)

    assert result["used_days"] == 0.0
    assert result["remaining_days"] == 25.0


def test_get_hr_violations_returns_all_violations():
    reports = {
        "userreports": [
            {
                "users_id": 1,
                "users_name": "Alice",
                "year": 2024,
                "diff": 360000,  # 100 hours
                "overtime_carryover": 0,
                "holidays_quota": 20,
                "holidays_carry": 0,
                "sum_absence": {"regular_holidays": 5.0}
            },
            {
                "users_id": 2,
                "users_name": "Bob",
                "year": 2024,
                "diff": 36000,  # 10 hours
                "overtime_carryover": 0,
                "holidays_quota": 25,
                "holidays_carry": 0,
                "sum_absence": {"regular_holidays": 15.0}
            },
        ]
    }

    config = {
        "max_overtime_hours": 80,
        "min_vacation_days": 10,
        "max_vacation_remaining": 20
    }

    violations = get_hr_violations(reports, config)

    assert len(violations) == 2
    assert violations[0]["user_id"] == 1
    assert violations[0]["user_name"] == "Alice"
    assert len(violations[0]["violations"]) == 2
    assert violations[0]["violations"][0]["type"] == "excessive_overtime"
    assert violations[0]["violations"][1]["type"] == "insufficient_vacation_taken"

    assert violations[1]["user_id"] == 2
    assert violations[1]["user_name"] == "Bob"
    assert len(violations[1]["violations"]) == 0


def test_get_hr_violations_returns_empty_for_no_violations():
    reports = {
        "userreports": [
            {
                "users_id": 1,
                "users_name": "Alice",
                "year": 2024,
                "diff": 36000,  # 10 hours
                "overtime_carryover": 0,
                "holidays_quota": 25,
                "holidays_carry": 0,
                "sum_absence": {"regular_holidays": 15.0}
            },
        ]
    }

    config = {
        "max_overtime_hours": 80,
        "min_vacation_days": 10,
        "max_vacation_remaining": 15
    }

    violations = get_hr_violations(reports, config)

    assert len(violations) == 1
    assert len(violations[0]["violations"]) == 0
