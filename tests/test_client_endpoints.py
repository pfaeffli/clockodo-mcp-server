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


@respx.mock
def test_get_user_reports_calls_clockodo_with_year_parameter():
    client = ClockodoClient(api_user="u@example.com", api_key="k", user_agent="ua")

    # userreports is a v1 endpoint: /api/userreports not /api/v2/userreports
    v1_url = DEFAULT_BASE_URL.replace("/api/v2/", "/api/")
    route = respx.get(f"{v1_url}userreports").mock(
        return_value=httpx.Response(
            200,
            json={
                "userreports": [
                    {
                        "users_id": 1,
                        "users_name": "Alice",
                        "year": 2024,
                        "sum_hours": 144000,
                        "sum_target": 140400,
                        "diff": 3600,
                        "overtime_carryover": 7200,
                        "overtime_reduced": 0,
                        "holidays_quota": 25,
                        "holidays_carry": 2.5,
                    }
                ]
            },
        )
    )

    data = client.get_user_reports(year=2024)

    # Request was made with year parameter
    assert route.called
    assert route.calls[0].request.url.params.get("year") == "2024"

    # Headers set
    sent_headers = route.calls[0].request.headers
    assert sent_headers.get("X-ClockodoApiUser") == "u@example.com"
    assert sent_headers.get("X-ClockodoApiKey") == "k"

    # Response parsed
    assert data["userreports"][0]["users_name"] == "Alice"
    assert data["userreports"][0]["diff"] == 3600


@respx.mock
def test_get_user_reports_with_user_id_parameter():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    # userreports is a v1 endpoint: /api/userreports not /api/v2/userreports
    v1_url = DEFAULT_BASE_URL.replace("/api/v2/", "/api/")
    route = respx.get(f"{v1_url}userreports").mock(
        return_value=httpx.Response(
            200,
            json={
                "userreports": [
                    {
                        "users_id": 42,
                        "users_name": "Bob",
                        "year": 2024,
                    }
                ]
            },
        )
    )

    data = client.get_user_reports(year=2024, user_id=42, type_level=1)

    # Request includes user_id and type parameters
    assert route.called
    assert route.calls[0].request.url.params.get("users_id") == "42"
    assert route.calls[0].request.url.params.get("type") == "1"
    assert data["userreports"][0]["users_id"] == 42
