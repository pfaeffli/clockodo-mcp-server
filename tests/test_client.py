import httpx
import respx
import pytest

from clockodo_mcp.client import ClockodoClient, DEFAULT_BASE_URL


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


@respx.mock
def test_client_error_handling_with_json_response():
    """Test that HTTP errors with JSON bodies are properly handled."""
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    respx.get(f"{DEFAULT_BASE_URL}users").mock(
        return_value=httpx.Response(
            400, json={"error": {"message": "Invalid request", "fields": ["field1"]}}
        )
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        client.list_users()

    # Check that the error detail is included (logged but not in exception message)
    assert "400" in str(exc_info.value)


@respx.mock
def test_client_error_handling_without_json_response():
    """Test that HTTP errors without JSON bodies are properly handled."""
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    respx.get(f"{DEFAULT_BASE_URL}users").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.list_users()


@respx.mock
def test_get_user_reports_v1_api():
    """Test get_user_reports uses v1 API endpoint correctly."""
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    # v1 API: /api/userreports (not /api/v2/userreports)
    v1_url = DEFAULT_BASE_URL.replace("/api/v2/", "/api/")
    route = respx.get(f"{v1_url}userreports").mock(
        return_value=httpx.Response(
            200, json={"userreports": [{"users_id": 1, "year": 2024, "diff": 36000}]}
        )
    )

    data = client.get_user_reports(year=2024)

    assert route.called
    assert route.calls[0].request.url.params.get("year") == "2024"
    assert route.calls[0].request.url.params.get("type") == "0"
    assert data["userreports"][0]["users_id"] == 1


@respx.mock
def test_get_user_reports_with_user_filter():
    """Test get_user_reports with user_id filter."""
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    v1_url = DEFAULT_BASE_URL.replace("/api/v2/", "/api/")
    route = respx.get(f"{v1_url}userreports").mock(
        return_value=httpx.Response(
            200, json={"userreports": [{"users_id": 42, "year": 2024}]}
        )
    )

    client.get_user_reports(year=2024, user_id=42, type_level=2)

    assert route.called
    assert route.calls[0].request.url.params.get("year") == "2024"
    assert route.calls[0].request.url.params.get("users_id") == "42"
    assert route.calls[0].request.url.params.get("type") == "2"


@respx.mock
def test_get_user_reports_error_handling():
    """Test get_user_reports v1 API error handling."""
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    v1_url = DEFAULT_BASE_URL.replace("/api/v2/", "/api/")
    respx.get(f"{v1_url}userreports").mock(
        return_value=httpx.Response(
            403, json={"error": {"message": "Forbidden - Insufficient permissions"}}
        )
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        client.get_user_reports(year=2024)

    assert "403" in str(exc_info.value)


@respx.mock
def test_get_user_reports_error_without_json():
    """Test get_user_reports v1 API error without JSON body."""
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    v1_url = DEFAULT_BASE_URL.replace("/api/v2/", "/api/")
    respx.get(f"{v1_url}userreports").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.get_user_reports(year=2024)
