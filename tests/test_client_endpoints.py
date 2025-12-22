import respx
import httpx

from clockodo_mcp.client import ClockodoClient, DEFAULT_BASE_URL


@respx.mock
def test_list_users_calls_clockodo_and_returns_json(monkeypatch):
    client = ClockodoClient(api_user="u@example.com", api_key="k", user_agent="ua")

    route = respx.get(f"{DEFAULT_BASE_URL}users").mock(
        return_value=httpx.Response(200, json={"users": [{"id": 1, "name": "Alice"}]})
    )

    data = client.list_users()

    # Request was made
    assert route.called

    # Headers set
    sent_headers = route.calls[0].request.headers
    assert sent_headers.get("X-ClockodoApiUser") == "u@example.com"
    assert sent_headers.get("X-ClockodoApiKey") == "k"
    assert sent_headers.get("User-Agent") == "ua"

    # Response parsed
    assert data["users"][0]["name"] == "Alice"
