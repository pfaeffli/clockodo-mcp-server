from __future__ import annotations


def analyze_overtime(report: dict, max_hours_threshold: float) -> dict:
    """
    Analyze overtime for a single user report.

    Args:
        report: User report data from Clockodo API
        max_hours_threshold: Maximum allowed overtime hours

    Returns:
        Dictionary with overtime analysis results
    """
    # Convert seconds to hours
    diff_seconds = report.get("diff", 0)
    carryover_seconds = report.get("overtime_carryover", 0)

    diff_hours = diff_seconds / 3600
    carryover_hours = carryover_seconds / 3600
    total_overtime = diff_hours + carryover_hours

    has_violation = total_overtime > max_hours_threshold

    result = {
        "has_violation": has_violation,
        "overtime_hours": total_overtime,
        "threshold": max_hours_threshold,
    }

    if has_violation:
        result["excess_hours"] = total_overtime - max_hours_threshold

    return result


def analyze_vacation(
    report: dict, min_days_used: float, max_days_remaining: float
) -> dict:
    """
    Analyze vacation usage for a single user report.

    Args:
        report: User report data from Clockodo API
        min_days_used: Minimum vacation days that should be used
        max_days_remaining: Maximum vacation days that can remain unused

    Returns:
        Dictionary with vacation analysis results
    """
    quota = report.get("holidays_quota", 0)
    carry = report.get("holidays_carry", 0)
    sum_absence = report.get("sum_absence", {})
    used = sum_absence.get("regular_holidays", 0.0)

    total_available = quota + carry
    remaining = total_available - used

    result = {
        "used_days": used,
        "remaining_days": remaining,
        "total_available": total_available,
        "has_violation": False,
    }

    # Check if too many vacation days remaining (higher priority)
    if remaining > max_days_remaining:
        result["has_violation"] = True
        result["violation_type"] = "excessive_vacation_remaining"
        result["excess_days"] = remaining - max_days_remaining

    # Check if too few vacation days used
    elif used < min_days_used:
        result["has_violation"] = True
        result["violation_type"] = "insufficient_vacation_taken"
        result["days_short"] = min_days_used - used

    return result


def get_hr_violations(reports: dict, config: dict) -> list[dict]:
    """
    Get list of all HR violations across all users.

    Args:
        reports: User reports data from Clockodo API
        config: Configuration with thresholds
            - max_overtime_hours: Maximum overtime threshold
            - min_vacation_days: Minimum vacation days to use
            - max_vacation_remaining: Maximum vacation days that can remain

    Returns:
        List of dictionaries with user violations
    """
    violations = []

    for report in reports.get("userreports", []):
        user_violations = {
            "user_id": report["users_id"],
            "user_name": report["users_name"],
            "year": report["year"],
            "violations": [],
        }

        # Check overtime
        overtime_result = analyze_overtime(report, config["max_overtime_hours"])
        if overtime_result["has_violation"]:
            user_violations["violations"].append(
                {
                    "type": "excessive_overtime",
                    "overtime_hours": overtime_result["overtime_hours"],
                    "threshold": overtime_result["threshold"],
                    "excess_hours": overtime_result["excess_hours"],
                }
            )

        # Check vacation
        vacation_result = analyze_vacation(
            report, config["min_vacation_days"], config["max_vacation_remaining"]
        )
        if vacation_result["has_violation"]:
            violation = {
                "type": vacation_result["violation_type"],
                "used_days": vacation_result["used_days"],
                "remaining_days": vacation_result["remaining_days"],
            }
            if "days_short" in vacation_result:
                violation["days_short"] = vacation_result["days_short"]
            if "excess_days" in vacation_result:
                violation["excess_days"] = vacation_result["excess_days"]
            user_violations["violations"].append(violation)

        violations.append(user_violations)

    return violations
