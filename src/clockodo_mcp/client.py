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

import os
import logging
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


DEFAULT_BASE_URL = "https://my.clockodo.com/api/v2/"


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
            f"CLOCKODO_API_USER={'SET' if api_user else 'MISSING'}, "
            f"CLOCKODO_API_KEY={'SET' if api_key else 'MISSING'}, "
            f"CLOCKODO_USER_AGENT={'SET' if user_agent else 'NOT_SET'}, "
            f"CLOCKODO_BASE_URL={base_url}, "
            f"CLOCKODO_EXTERNAL_APP_CONTACT={'SET' if external_app_contact else 'NOT_SET'}"
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
            "X-Clockodo-External-Application": f"{app_name}; {contact}",
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
        resp.raise_for_status()
        return resp.json()

    # ==============================================
    # API Endpoints
    # ==============================================

    def list_users(self) -> dict:
        """
        List all users from Clockodo.

        Returns:
            Dictionary with 'users' key containing list of user objects
        """
        return self._request("GET", "users")

    def get_user_reports(
        self, year: int, user_id: int | None = None, type_level: int = 0
    ) -> dict:
        """
        Get user reports for a specific year.

        Follows Pattern #5 (API Version Handling):
        - userreports is a legacy v1 endpoint
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

        # userreports is v1 API: /api/userreports not /api/v2/userreports
        v1_base_url = self.base_url.replace("/api/v2/", "/api/")
        url = f"{v1_base_url}userreports"

        resp = httpx.request(
            method="GET",
            url=url,
            headers=self.default_headers,
            params=params,
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()
