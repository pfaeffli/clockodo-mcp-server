"""Tests for SSE transport hardening and the --version flag."""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from clockodo_mcp import server
from clockodo_mcp.transport_security import (
    BearerTokenMiddleware,
    build_transport_security,
    is_loopback_host,
    validate_sse_auth,
)


def _client(token="s3cret"):
    app = Starlette(routes=[Route("/", lambda r: PlainTextResponse("ok"))])
    return TestClient(BearerTokenMiddleware(app, token))


def test_middleware_accepts_valid_token():
    resp = _client().get("/", headers={"Authorization": "Bearer s3cret"})
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic s3cret"}],
)
def test_middleware_rejects_bad_or_missing_token(headers):
    resp = _client().get("/", headers=headers)
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "[::1]"])
def test_loopback_hosts(host):
    assert is_loopback_host(host)


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.5", "example.com", "::"])
def test_non_loopback_hosts(host):
    assert not is_loopback_host(host)


def test_validate_requires_token_on_non_loopback():
    with pytest.raises(ValueError, match="CLOCKODO_MCP_AUTH_TOKEN"):
        validate_sse_auth("0.0.0.0", None)
    validate_sse_auth("0.0.0.0", "tok")
    validate_sse_auth("127.0.0.1", None)


def test_transport_security_always_on():
    settings = build_transport_security(["example.com:*"])
    assert settings.enable_dns_rebinding_protection
    assert settings.allowed_hosts == ["example.com:*"]
    assert "http://example.com:*" in settings.allowed_origins


def test_version_flag_prints_and_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        server.main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.startswith("clockodo-mcp ")
