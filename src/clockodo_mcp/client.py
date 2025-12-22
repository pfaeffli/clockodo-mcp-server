from __future__ import annotations

import os
from dataclasses import dataclass
import httpx


DEFAULT_BASE_URL = "https://my.clockodo.com/api/v2/"


@dataclass
class ClockodoClient:
    api_user: str
    api_key: str
    user_agent: str | None = None
    base_url: str = DEFAULT_BASE_URL
    external_app_contact: str | None = None

    @classmethod
    def from_env(cls) -> "ClockodoClient":
        api_user = os.getenv("CLOCKODO_API_USER", "")
        api_key = os.getenv("CLOCKODO_API_KEY", "")
        user_agent = os.getenv("CLOCKODO_USER_AGENT")
        base_url = os.getenv("CLOCKODO_BASE_URL", DEFAULT_BASE_URL)
        external_app_contact = os.getenv("CLOCKODO_EXTERNAL_APP_CONTACT")
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

    # User Endpoints
    def list_users(self) -> dict:
        """List all users."""
        return self._request("GET", "users")

    def get_user_reports(
        self, year: int, user_id: int | None = None, type_level: int = 0
    ) -> dict:
        """Get user reports for a specific year."""
        params = {"year": year, "type": type_level}
        if user_id is not None:
            params["users_id"] = user_id
        return self._request("GET", "userreports", params=params)
