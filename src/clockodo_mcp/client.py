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
import time
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


DEFAULT_BASE_URL = "https://my.clockodo.com/api/"

MAX_PAGES = 100
MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5
RETRY_MAX_DELAY = 10.0
RETRY_STATUSES = frozenset({429, 502, 503, 504})
IDEMPOTENT_METHODS = frozenset({"GET", "PUT", "DELETE"})


@dataclass
class ClockodoClient:  # pylint: disable=too-many-public-methods
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
    _http: httpx.Client | None = field(default=None, init=False, repr=False)

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

    @property
    def http(self) -> httpx.Client:
        """Shared HTTP client (created lazily, reuses connections)."""
        if self._http is None:
            self._http = httpx.Client(headers=self.default_headers, timeout=30.0)
        return self._http

    def close(self) -> None:
        """Close the shared HTTP client."""
        if self._http is not None:
            self._http.close()
            self._http = None

    def _sleep(self, seconds: float) -> None:
        """Sleep between retries (separate method so tests can patch it)."""
        time.sleep(seconds)

    @staticmethod
    def _retry_delay(attempt: int, response: httpx.Response | None) -> float:
        """Exponential backoff (0.5, 1, 2 s), honouring Retry-After seconds."""
        delay = RETRY_BASE_DELAY * 2**attempt
        if response is not None:
            try:
                delay = float(response.headers["Retry-After"])
            except (KeyError, ValueError):
                pass
        return min(max(delay, 0.0), RETRY_MAX_DELAY)

    def _send(
        self,
        method: str,
        url: str,
        params: dict | None,
        json_data: dict | None,
        timeout: float,
    ) -> httpx.Response:
        """Send a request, retrying idempotent methods on transient failures."""
        retries = MAX_RETRIES if method.upper() in IDEMPOTENT_METHODS else 0
        attempt = 0
        while True:
            try:
                resp = self.http.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                    timeout=timeout,
                )
            except httpx.TransportError as e:
                if attempt >= retries:
                    raise
                logger.warning("%s %s failed (%s), retrying", method, url, e)
                self._sleep(self._retry_delay(attempt, None))
            else:
                if resp.status_code not in RETRY_STATUSES or attempt >= retries:
                    return resp
                logger.warning(
                    "%s %s returned %s, retrying", method, url, resp.status_code
                )
                self._sleep(self._retry_delay(attempt, resp))
            attempt += 1

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

        Idempotent methods (GET, PUT, DELETE) are retried up to 3 times on
        429/502/503/504 and transport errors; POST is never retried.

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
        resp = self._send(method, url, params, json_data, timeout)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Include response body in the error message for better debugging
            try:
                error_detail = resp.json()
            except ValueError:
                raise e from None
            logger.error("API Error: %s - %s", e, error_detail)
            # Re-raise with detail in message
            raise httpx.HTTPStatusError(
                f"{e} - Details: {error_detail}",
                request=e.request,
                response=e.response,
            ) from e
        return resp.json()

    def _get_all_pages(
        self, endpoint: str, key: str, params: dict | None = None
    ) -> dict:
        """
        GET a paged endpoint and concatenate the list under `key` over all pages.

        Follows pages until current_page >= count_pages (at most MAX_PAGES).
        The result is the last page's response with the full list under `key`
        (the list may come as 'data', which is normalized to `key`).
        """
        items: list = []
        page = 1
        while True:
            page_params = dict(params or {})
            if page > 1:
                page_params["page"] = page
            resp = self._request("GET", endpoint, params=page_params or None)
            items.extend(resp.get(key) or resp.get("data") or [])
            paging = resp.get("paging") or {}
            if (
                paging.get("current_page", page) >= paging.get("count_pages", 1)
                or page >= MAX_PAGES
            ):
                break
            page += 1
        if page >= MAX_PAGES and paging.get("current_page", page) < paging.get(
            "count_pages", 1
        ):
            logger.warning("Stopped paging %s after %s pages", endpoint, MAX_PAGES)
        resp[key] = items
        return resp

    # ==============================================
    # API Endpoints
    # ==============================================

    def list_users(self) -> dict:
        """
        List all users from Clockodo (v3 API).

        Returns:
            Dictionary with 'users' key containing list of user objects
        """
        return self._get_all_pages("v3/users", "users")

    def get_me(self) -> dict:
        """Get the authenticated user (v4 API): `{"data": {...}}`."""
        return self._request("GET", "v4/users/me")

    def list_customers(self) -> dict:
        """
        List all customers from Clockodo (v3 API).

        Returns:
            Dictionary with 'customers' key containing list of customer objects
        """
        return self._get_all_pages("v3/customers", "customers")

    def list_services(self) -> dict:
        """
        List all services from Clockodo (v4 API).

        Returns:
            Dictionary with 'services' key containing list of service objects
        """
        return self._get_all_pages("v4/services", "services")

    def list_projects(self) -> dict:
        """
        List all projects from Clockodo (v4 API).

        Returns:
            Dictionary with 'projects' key containing list of project objects
        """
        return self._get_all_pages("v4/projects", "projects")

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
        return self._request("GET", "userreports", params=params)

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
        return self._get_all_pages("v2/entries", "entries", params=params)

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

    def get_entry(self, entry_id: int) -> dict:
        """Get a single entry (v2 API)."""
        return self._request("GET", f"v2/entries/{entry_id}")

    def edit_entry(self, entry_id: int, data: dict) -> dict:
        """Edit an existing time entry."""
        return self._request("PUT", f"v2/entries/{entry_id}", json_data=data)

    def delete_entry(self, entry_id: int) -> dict:
        """Delete a time entry."""
        return self._request("DELETE", f"v2/entries/{entry_id}")

    # ==============================================
    # Absences (v4)
    # ==============================================

    def list_absences(
        self,
        year: int,
        user_id: int | None = None,
        absence_type: int | None = None,
    ) -> dict:
        """
        List absences for a year (v4 API).

        Args:
            year: Calendar year to list absences for
            user_id: Optional user ID to filter absences
            absence_type: Optional absence type to filter absences
        """
        params: dict[str, int] = {"filter[year]": year}
        if user_id is not None:
            params["filter[users_id]"] = user_id
        if absence_type is not None:
            params["filter[type]"] = absence_type
        resp = self._request("GET", "v4/absences", params=params)
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
        half_day: bool = False,
        sick_note: bool | None = None,
    ) -> dict:
        """
        Create a new absence (vacation, etc.).

        Args:
            date_since: Start date (YYYY-MM-DD)
            date_until: End date (YYYY-MM-DD)
            absence_type: Type of absence (1: Vacation, 2: Special leave, 4: Sick day, etc.)
            user_id: Optional user ID (if admin)
            status: Optional status (0: Enquired, 1: Approved, 2: Declined)
            half_day: Book a half day (Clockodo allows this for a single day only)
            sick_note: Whether a sick note exists (required by Clockodo for
                types 4 and 5, sick day and sick day of a child)
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
        if half_day:
            data["half_day"] = True
        if sick_note is not None:
            data["sick_note"] = sick_note
        return self._request("POST", "v4/absences", json_data=data)

    def get_me(self) -> dict:
        """Get the user the API credentials belong to."""
        return self._request("GET", "v3/users/me")

    def get_absence(self, absence_id: int) -> dict:
        """Get a single absence (v4 API)."""
        return self._request("GET", f"v4/absences/{absence_id}")

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
