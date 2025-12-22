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

    @classmethod
    def from_env(cls) -> "ClockodoClient":
        api_user = os.getenv("CLOCKODO_API_USER", "")
        api_key = os.getenv("CLOCKODO_API_KEY", "")
        user_agent = os.getenv("CLOCKODO_USER_AGENT")
        base_url = os.getenv("CLOCKODO_BASE_URL", DEFAULT_BASE_URL)
        return cls(api_user=api_user, api_key=api_key, user_agent=user_agent, base_url=base_url)

    @property
    def default_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "X-ClockodoApiUser": self.api_user,
            "X-ClockodoApiKey": self.api_key,
        }
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        else:
            # Provide a minimal default user agent if not set explicitly
            headers["User-Agent"] = "clockodo-mcp/unknown"
        return headers

    # Endpoints
    def list_users(self) -> dict:
        url = f"{self.base_url}users"
        resp = httpx.get(url, headers=self.default_headers, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
