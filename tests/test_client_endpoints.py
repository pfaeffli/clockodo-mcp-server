import httpx
import respx

from clockodo_mcp.client import DEFAULT_BASE_URL, ClockodoClient


@respx.mock
def test_list_users_calls_clockodo_and_returns_json(monkeypatch):
    client = ClockodoClient(api_user="u@example.com", api_key="k", user_agent="ua")

    route = respx.get(f"{DEFAULT_BASE_URL}v3/users").mock(
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
def test_list_users_normalization():
    """Test that list_users handles 'data' key in response."""
    client = ClockodoClient(api_user="u", api_key="k")

    # Mock response with 'data' instead of 'users'
    respx.get(f"{DEFAULT_BASE_URL}v3/users").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": 1, "name": "Alice"}], "paging": {"count_items": 1}},
        )
    )

    resp = client.list_users()
    assert "users" in resp
    assert resp["users"][0]["name"] == "Alice"


@respx.mock
def test_get_user_reports_calls_clockodo_with_year_parameter():
    client = ClockodoClient(api_user="u@example.com", api_key="k", user_agent="ua")

    route = respx.get(f"{DEFAULT_BASE_URL}userreports").mock(
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

    route = respx.get(f"{DEFAULT_BASE_URL}userreports").mock(
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


@respx.mock
def test_list_customers_calls_clockodo_and_returns_json():
    client = ClockodoClient(api_user="u@example.com", api_key="k", user_agent="ua")

    route = respx.get(f"{DEFAULT_BASE_URL}v3/customers").mock(
        return_value=httpx.Response(
            200, json={"customers": [{"id": 100, "name": "Customer A"}]}
        )
    )

    data = client.list_customers()

    assert route.called
    assert data["customers"][0]["name"] == "Customer A"


@respx.mock
def test_list_customers_normalization():
    """Test that list_customers handles 'data' key in response."""
    client = ClockodoClient(api_user="u", api_key="k")

    # Mock response with 'data' instead of 'customers'
    respx.get(f"{DEFAULT_BASE_URL}v3/customers").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": 100, "name": "Customer A"}],
                "paging": {"count_items": 1},
            },
        )
    )

    resp = client.list_customers()
    assert "customers" in resp
    assert resp["customers"][0]["name"] == "Customer A"


@respx.mock
def test_list_services_calls_clockodo_and_returns_json():
    client = ClockodoClient(api_user="u@example.com", api_key="k", user_agent="ua")

    route = respx.get(f"{DEFAULT_BASE_URL}v4/services").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": 200, "name": "Service X"}]}
        )
    )

    data = client.list_services()

    assert route.called
    assert data["services"][0]["name"] == "Service X"
