"""
HR compliance service for analyzing employee work data.

This module implements the service layer for HR functionality.

Pattern: Service Layer (Layer 2)
- Contains business logic
- Orchestrates client calls and data analysis
- No MCP protocol handling
- Uses dependency injection

Architecture: Server → Service → Client
"""
from __future__ import annotations

from ..client import ClockodoClient
from ..hr_analyzer import analyze_overtime, analyze_vacation, get_hr_violations


class HRService:
    """
    Service for HR compliance checking and reporting.

    Follows Pattern #3 (Dependency Injection):
    - Client injected via constructor
    - Testable by mocking client
    - Clear dependency graph

    Follows Pattern #4 (Separation of Concerns):
    - Orchestrates API calls (via client)
    - Delegates analysis (to hr_analyzer)
    - Returns structured data
    """

    def __init__(self, client: ClockodoClient):
        """
        Initialize HR service.

        Args:
            client: Clockodo API client for fetching data
        """
        self.client = client

    def check_overtime_compliance(
        self, year: int, max_overtime_hours: float = 80
    ) -> dict:
        """
        Check which employees have excessive overtime.

        Args:
            year: Year to check (e.g., 2024)
            max_overtime_hours: Maximum allowed overtime hours (default: 80)

        Returns:
            Dictionary with overtime violations
        """
        reports = self.client.get_user_reports(year=year)

        violations = []
        for report in reports.get("userreports", []):
            overtime_result = analyze_overtime(report, max_overtime_hours)
            if overtime_result["has_violation"]:
                violations.append(
                    {
                        "user_id": report["users_id"],
                        "user_name": report["users_name"],
                        "overtime_hours": overtime_result["overtime_hours"],
                        "threshold": overtime_result["threshold"],
                        "excess_hours": overtime_result["excess_hours"],
                    }
                )

        return {
            "year": year,
            "threshold": max_overtime_hours,
            "total_violations": len(violations),
            "violations": violations,
        }

    def check_vacation_compliance(
        self, year: int, min_vacation_days: float = 10, max_vacation_remaining: float = 20
    ) -> dict:
        """
        Check which employees have vacation compliance issues.

        Args:
            year: Year to check (e.g., 2024)
            min_vacation_days: Minimum vacation days that should be used (default: 10)
            max_vacation_remaining: Maximum vacation days that can remain unused (default: 20)

        Returns:
            Dictionary with vacation violations
        """
        reports = self.client.get_user_reports(year=year)

        violations = []
        for report in reports.get("userreports", []):
            vacation_result = analyze_vacation(
                report, min_vacation_days, max_vacation_remaining
            )
            if vacation_result["has_violation"]:
                violation = {
                    "user_id": report["users_id"],
                    "user_name": report["users_name"],
                    "violation_type": vacation_result["violation_type"],
                    "used_days": vacation_result["used_days"],
                    "remaining_days": vacation_result["remaining_days"],
                }
                if "days_short" in vacation_result:
                    violation["days_short"] = vacation_result["days_short"]
                if "excess_days" in vacation_result:
                    violation["excess_days"] = vacation_result["excess_days"]
                violations.append(violation)

        return {
            "year": year,
            "min_vacation_days": min_vacation_days,
            "max_vacation_remaining": max_vacation_remaining,
            "total_violations": len(violations),
            "violations": violations,
        }

    def get_hr_summary(
        self,
        year: int,
        max_overtime_hours: float = 80,
        min_vacation_days: float = 10,
        max_vacation_remaining: float = 20,
    ) -> dict:
        """
        Get complete HR compliance summary for all employees.

        Args:
            year: Year to check (e.g., 2024)
            max_overtime_hours: Maximum allowed overtime hours (default: 80)
            min_vacation_days: Minimum vacation days that should be used (default: 10)
            max_vacation_remaining: Maximum vacation days that can remain unused (default: 20)

        Returns:
            Dictionary with complete HR summary including all violations
        """
        reports = self.client.get_user_reports(year=year)

        config = {
            "max_overtime_hours": max_overtime_hours,
            "min_vacation_days": min_vacation_days,
            "max_vacation_remaining": max_vacation_remaining,
        }

        all_violations = get_hr_violations(reports, config)
        employees_with_violations = [v for v in all_violations if len(v["violations"]) > 0]

        return {
            "year": year,
            "total_employees": len(reports.get("userreports", [])),
            "employees_with_violations": employees_with_violations,
            "total_employees_with_violations": len(employees_with_violations),
            "config": config,
        }
