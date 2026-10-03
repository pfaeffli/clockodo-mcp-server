"""Tests for the server entry point (main, --version, SSE start-up)."""

import asyncio
import dataclasses
from unittest.mock import MagicMock

import pytest

from clockodo_mcp import server
from clockodo_mcp.transport_security import BearerTokenMiddleware


def _use_config(monkeypatch, **changes):
    monkeypatch.setattr(server, "config", dataclasses.replace(server.config, **changes))


def test_main_version_prints_and_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        server.main(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out.startswith("clockodo-mcp ")


def test_main_runs_stdio(monkeypatch):
    _use_config(monkeypatch, transport="stdio")
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)

    server.main([])

    run.assert_called_once_with(transport="stdio")


def test_main_sse_on_loopback_without_token(monkeypatch):
    _use_config(
        monkeypatch, transport="sse", host="127.0.0.1", port=8123, auth_token=None
    )
    uvicorn_run = MagicMock()
    monkeypatch.setattr(server.uvicorn, "run", uvicorn_run)

    server.main([])

    app = uvicorn_run.call_args.args[0]
    assert not isinstance(app, BearerTokenMiddleware)
    assert uvicorn_run.call_args.kwargs == {"host": "127.0.0.1", "port": 8123}


def test_main_sse_with_token_wraps_app(monkeypatch):
    _use_config(
        monkeypatch, transport="sse", host="0.0.0.0", port=8123, auth_token="s3cret"
    )
    uvicorn_run = MagicMock()
    monkeypatch.setattr(server.uvicorn, "run", uvicorn_run)

    server.main([])

    assert isinstance(uvicorn_run.call_args.args[0], BearerTokenMiddleware)


def test_main_sse_refuses_public_host_without_token(monkeypatch):
    _use_config(monkeypatch, transport="sse", host="0.0.0.0", auth_token=None)
    uvicorn_run = MagicMock()
    monkeypatch.setattr(server.uvicorn, "run", uvicorn_run)

    with pytest.raises(ValueError, match="CLOCKODO_MCP_AUTH_TOKEN"):
        server.main([])

    uvicorn_run.assert_not_called()


def test_bearer_middleware_passes_non_http_scopes():
    calls = []

    async def app(scope, receive, send):
        calls.append(scope["type"])

    middleware = BearerTokenMiddleware(app, "s3cret")
    asyncio.run(middleware({"type": "lifespan"}, None, None))

    assert calls == ["lifespan"]
