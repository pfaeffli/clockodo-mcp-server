from clockodo_mcp.client import ClockodoClient


def test_clockodo_client_builds_auth_headers_from_env(monkeypatch):
    monkeypatch.setenv("CLOCKODO_API_USER", "user@example.com")
    monkeypatch.setenv("CLOCKODO_API_KEY", "secretkey")
    monkeypatch.setenv("CLOCKODO_USER_AGENT", "clockodo-mcp/0.1.0")

    client = ClockodoClient.from_env()

    headers = client.default_headers
    assert headers["X-ClockodoApiUser"] == "user@example.com"
    assert headers["X-ClockodoApiKey"] == "secretkey"
    assert headers["User-Agent"].startswith("clockodo-mcp/")


def test_clockodo_client_base_url_default():
    client = ClockodoClient(api_user="u", api_key="k")
    assert client.base_url.endswith("/api/v2/")
