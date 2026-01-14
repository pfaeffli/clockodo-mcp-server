"""
Clockodo API Client.

This module provides a thin HTTP client layer for the Clockodo REST API.

Pattern: Pure HTTP client - no business logic
- Only handles HTTP communication
- Returns raw API responses
- Lets errors bubble up via httpx.raise_for_status()
- Uses dependency injection (constructor parameters)
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


DEFAULT_BASE_URL = "https://my.clockodo.com/api/"


@dataclass
class ClockodoClient:
    """
    HTTP client for Clockodo REST API.

    Follows Pattern #3 (Dependency Injection):
    - All dependencies via constructor
    - Testable by mocking
    - No global state
    """

    api_user: str
    api_key: str
    user_agent: str | None = None
    base_url: str = DEFAULT_BASE_URL
    external_app_contact: str | None = None

    def __post_init__(self):
        """Normalize base_url to always end with /api/ and no version prefix."""
        # Ensure trailing slash
        if not self.base_url.endswith("/"):
            self.base_url += "/"

        # Strip version suffixes like /v2/, /v3/, /v4/
        self.base_url = re.sub(r"v\d+/?$", "", self.base_url)

        # Ensure it ends with /api/
        if not self.base_url.endswith("/api/"):
            if self.base_url.endswith("/api"):
                self.base_url += "/"
            elif "/api/" not in self.base_url:
                # If it's just a domain or path without /api/, append it
                # but only if it's not already there
                self.base_url = self.base_url.rstrip("/") + "/api/"

    @classmethod
    def from_env(cls) -> "ClockodoClient":
        """
        Create client from environment variables.

        Follows Pattern #2 (Configuration Management):
        - All config from environment
        - Safe defaults
        """
        api_user = os.getenv("CLOCKODO_API_USER", "")
        api_key = os.getenv("CLOCKODO_API_KEY", "")
        user_agent = os.getenv("CLOCKODO_USER_AGENT")
        base_url = os.getenv("CLOCKODO_BASE_URL", DEFAULT_BASE_URL)
        external_app_contact = os.getenv("CLOCKODO_EXTERNAL_APP_CONTACT")

        # Log environment variable status (mask sensitive values)
        logger.info(
            "ClockodoClient.from_env() - Environment variables: "
            "CLOCKODO_API_USER=%s, "
            "CLOCKODO_API_KEY=%s, "
            "CLOCKODO_USER_AGENT=%s, "
            "CLOCKODO_BASE_URL=%s, "
            "CLOCKODO_EXTERNAL_APP_CONTACT=%s",
            "SET" if api_user else "MISSING",
            "SET" if api_key else "MISSING",
            "SET" if user_agent else "NOT_SET",
            base_url,
            "SET" if external_app_contact else "NOT_SET",
        )

        return cls(
            api_user=api_user,
            api_key=api_key,
            user_agent=user_agent,
            base_url=base_url,
            external_app_contact=external_app_contact,
        )

    @property
    def default_headers(self) -> dict[str, str]:
        app_name = self.user_agent or "clockodo-mcp"
        contact = self.external_app_contact or self.api_user
        headers: dict[str, str] = {
            "X-ClockodoApiUser": self.api_user,
            "X-ClockodoApiKey": self.api_key,
            "X-Clockodo-External-Application": f"{app_name};{contact}",
        }
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        else:
            # Provide a minimal default user agent if not set explicitly
            headers["User-Agent"] = "clockodo-mcp/unknown"
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """
        Make HTTP request to Clockodo API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., "users", "entries")
            params: Query parameters
            json_data: JSON body for POST/PUT requests
            timeout: Request timeout in seconds

        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        resp = httpx.request(
            method=method,
            url=url,
            headers=self.default_headers,
            params=params,
            json=json_data,
            timeout=timeout,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Include response body in the error message for better debugging
            try:
                error_detail = resp.json()
                logger.error("API Error: %s - %s", e, error_detail)
                # Re-raise with detail in message
                raise httpx.HTTPStatusError(
                    f"{e} - Details: {error_detail}",
                    request=e.request,
                    response=e.response,
                ) from e
            except Exception as parse_error:
                raise e from parse_error
        return resp.json()

    # ==============================================
    # API Endpoints
    # ==============================================

    def list_users(self) -> dict:
        """
        List all users from Clockodo (v3 API).

        Returns:
            Dictionary with 'users' key containing list of user objects
        """
        resp = self._request("GET", "v3/users")
        # Normalize response (pattern change: 'data' instead of 'users')
        if "data" in resp and "users" not in resp:
            resp["users"] = resp["data"]
        return resp

    def list_customers(self) -> dict:
        """
        List all customers from Clockodo (v3 API).

        Returns:
            Dictionary with 'customers' key containing list of customer objects
        """
        resp = self._request("GET", "v3/customers")
        # Normalize response (pattern change: 'data' instead of 'customers')
        if "data" in resp and "customers" not in resp:
            resp["customers"] = resp["data"]
        return resp

    def list_services(self) -> dict:
        """
        List all services from Clockodo (v4 API).

        Returns:
            Dictionary with 'services' key containing list of service objects
        """
        resp = self._request("GET", "v4/services")
        # Normalize v4 response (pattern change: 'data' instead of 'services')
        if "data" in resp and "services" not in resp:
            resp["services"] = resp["data"]
        return resp

    def list_projects(self) -> dict:
        """
        List all projects from Clockodo (v4 API).

        Returns:
            Dictionary with 'projects' key containing list of project objects
        """
        resp = self._request("GET", "v4/projects")
        # Normalize v4 response (pattern change: 'data' instead of 'projects')
        if "data" in resp and "projects" not in resp:
            resp["projects"] = resp["data"]
        return resp

    def get_user_reports(
        self, year: int, user_id: int | None = None, type_level: int = 0
    ) -> dict:
        """
        Get user reports for a specific year.

        Follows Pattern #5 (API Version Handling):
        - userreports is a legacy v1 endpoint (no v2+ successor exists for this report)
        - Explicitly uses /api/ instead of /api/v2/

        Args:
            year: Year to fetch (e.g., 2024, 2025)
            user_id: Optional specific user ID to filter
            type_level: Report detail level (0=year only, up to 4=detailed)

        Returns:
            Dictionary with 'userreports' key containing list of report objects
        """
        params: dict[str, int] = {"year": year, "type": type_level}
        if user_id is not None:
            params["users_id"] = user_id

        # userreports is v1 API: /api/userreports
        url = f"{self.base_url}userreports"

        resp = httpx.request(
            method="GET",
            url=url,
            headers=self.default_headers,
            params=params,
            timeout=30.0,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                error_detail = resp.json()
                logger.error("API Error (v1): %s - %s", e, error_detail)
                raise httpx.HTTPStatusError(
                    f"{e} - Details: {error_detail}",
                    request=e.request,
                    response=e.response,
                ) from e
            except Exception as parse_error:
                raise e from parse_error
        return resp.json()

    # ==============================================
    # Clock Operations (v2 is the latest as of 2026-01-14)
    # ==============================================

    def get_clock(self) -> dict:
        """Get the currently running clock."""
        return self._request("GET", "v2/clock")

    def clock_start(
        self,
        customers_id: int,
        services_id: int,
        billable: int | None = None,
        projects_id: int | None = None,
        text: str | None = None,
    ) -> dict:
        """
        Start the clock.

        Args:
            customers_id: Customer ID
            services_id: Service ID
            billable: Optional billable flag (defaults to customer/project default if omitted)
            projects_id: Optional project ID
            text: Optional entry description
        """
        data: dict[str, int | str] = {
            "customers_id": customers_id,
            "services_id": services_id,
        }
        if billable is not None:
            data["billable"] = billable
        if projects_id is not None:
            data["projects_id"] = projects_id
        if text is not None:
            data["text"] = text
        return self._request("POST", "v2/clock", json_data=data)

    def clock_stop(self, entry_id: int) -> dict:
        """
        Stop the currently running clock.

        Args:
            entry_id: ID of the running clock entry to stop
        """
        return self._request("DELETE", f"v2/clock/{entry_id}")

    # ==============================================
    # Entries (v2 is the latest as of 2026-01-14)
    # ==============================================

    def list_entries(
        self,
        time_since: str,
        time_until: str,
        user_id: int | None = None,
    ) -> dict:
        """
        List time entries.

        Args:
            time_since: Start time in ISO 8601 UTC format (e.g., "2021-01-01T00:00:00Z")
            time_until: End time in ISO 8601 UTC format (e.g., "2021-02-01T00:00:00Z")
            user_id: Optional user ID to filter entries
        """
        params: dict[str, str | int] = {
            "time_since": time_since,
            "time_until": time_until,
        }
        if user_id is not None:
            params["filter[users_id]"] = user_id
        return self._request("GET", "v2/entries", params=params)

    def create_entry(
        self,
        customers_id: int,
        services_id: int,
        billable: int,
        time_since: str,
        time_until: str,
        projects_id: int | None = None,
        text: str | None = None,
        user_id: int | None = None,
    ) -> dict:
        """
        Create a new time entry.

        Args:
            customers_id: Customer ID
            services_id: Service ID
            billable: Billable flag (0, 1, or 2) - REQUIRED
            time_since: Start time in ISO 8601 UTC format (e.g., "2021-01-01T00:00:00Z")
            time_until: End time in ISO 8601 UTC format (e.g., "2021-02-01T00:00:00Z")
            projects_id: Optional project ID
            text: Optional entry description
            user_id: Optional user ID (for admin operations)
        """
        data = {
            "customers_id": customers_id,
            "services_id": services_id,
            "billable": billable,
            "time_since": time_since,
            "time_until": time_until,
        }
        if projects_id is not None:
            data["projects_id"] = projects_id
        if text is not None:
            data["text"] = text
        if user_id is not None:
            data["users_id"] = user_id
        return self._request("POST", "v2/entries", json_data=data)

    def edit_entry(self, entry_id: int, data: dict) -> dict:
        """Edit an existing time entry."""
        return self._request("PUT", f"v2/entries/{entry_id}", json_data=data)

    def delete_entry(self, entry_id: int) -> dict:
        """Delete a time entry."""
        return self._request("DELETE", f"v2/entries/{entry_id}")

    # ==============================================
    # Absences (v4)
    # ==============================================

    def list_absences(self, year: int) -> dict:
        """List absences for a year (v4 API)."""
        resp = self._request("GET", "v4/absences", params={"filter[year]": year})
        # Normalize v4 response
        if "data" in resp and "absences" not in resp:
            resp["absences"] = resp["data"]
        return resp

    def create_absence(
        self,
        date_since: str,
        date_until: str,
        absence_type: int,
        user_id: int | None = None,
        status: int | None = None,
    ) -> dict:
        """
        Create a new absence (vacation, etc.).

        Args:
            date_since: Start date (YYYY-MM-DD)
            date_until: End date (YYYY-MM-DD)
            absence_type: Type of absence (1: Vacation, 2: Illness, etc.)
            user_id: Optional user ID (if admin)
            status: Optional status (0: Enquired, 1: Approved, 2: Declined)
        """
        data = {
            "date_since": date_since,
            "date_until": date_until,
            "type": absence_type,
        }
        if user_id is not None:
            data["users_id"] = user_id
        if status is not None:
            data["status"] = status
        return self._request("POST", "v4/absences", json_data=data)

    def edit_absence(self, absence_id: int, data: dict) -> dict:
        """
        Edit an existing absence.

        Args:
            absence_id: Absence ID
            data: Dictionary with fields to update
        """
        return self._request("PUT", f"v4/absences/{absence_id}", json_data=data)

    def delete_absence(self, absence_id: int) -> dict:
        """Delete an absence."""
        return self._request("DELETE", f"v4/absences/{absence_id}")
