from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Callable, Optional

from .client import ClockodoClient


@dataclass
class _Server:
    tools: dict[str, Callable[[], object]]

    @property
    def tool_names(self) -> Iterable[str]:
        return self.tools.keys()


def _health() -> dict[str, str]:
    return {"status": "ok"}

def _list_users_tool(client: ClockodoClient) -> Callable[[], object]:
    def _call() -> object:
        return client.list_users()

    return _call


def create_server(client: Optional[ClockodoClient] = None) -> _Server:
    if client is None:
        client = ClockodoClient.from_env()

    tools: dict[str, Callable[[], object]] = {
        "health": _health,
        "list_users": _list_users_tool(client),
    }
    return _Server(tools=tools)


def main() -> None:
    # Placeholder main for future MCP stdio server startup
    server = create_server()
    # For now, just run health and print to signal the container started
    result = server.tools["health"]()
    print(result)
