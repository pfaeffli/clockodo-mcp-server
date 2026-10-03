"""SSE transport hardening: loopback detection, DNS-rebinding settings, bearer auth."""

from __future__ import annotations

import hmac
import ipaddress
from collections.abc import Sequence

from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def is_loopback_host(host: str) -> bool:
    """Return True if host is localhost or a loopback IP address."""
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def validate_sse_auth(host: str, auth_token: str | None) -> None:
    """Refuse non-loopback SSE binds without a bearer token."""
    if not is_loopback_host(host) and not auth_token:
        raise ValueError(
            f"Refusing to start SSE transport on non-loopback host {host!r} "
            "without authentication: set CLOCKODO_MCP_AUTH_TOKEN."
        )


def build_transport_security(allowed_hosts: Sequence[str]) -> TransportSecuritySettings:
    """DNS-rebinding protection, always on; origins derived from allowed hosts."""
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(allowed_hosts),
        allowed_origins=[f"http://{h}" for h in allowed_hosts]
        + [f"https://{h}" for h in allowed_hosts],
    )


class BearerTokenMiddleware:  # pylint: disable=too-few-public-methods
    """ASGI middleware requiring `Authorization: Bearer <token>` on HTTP requests."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self._token = token.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        supplied = b""
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                scheme, _, credential = value.partition(b" ")
                if scheme.lower() == b"bearer":
                    supplied = credential.strip()
                break
        if hmac.compare_digest(supplied, self._token):
            await self.app(scope, receive, send)
            return
        response = PlainTextResponse(
            "Unauthorized", status_code=401, headers={"WWW-Authenticate": "Bearer"}
        )
        await response(scope, receive, send)
