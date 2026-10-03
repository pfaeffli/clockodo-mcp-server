import httpx
import pytest
import respx

from clockodo_mcp.client import DEFAULT_BASE_URL, ClockodoClient


def _paging(page: int, pages: int) -> dict:
    return {
        "items_per_page": 2,
        "current_page": page,
        "count_pages": pages,
        "count_items": 3,
    }


class _Client(ClockodoClient):
    """Client that records sleeps instead of sleeping."""

    def __post_init__(self):
        super().__post_init__()
        self.sleeps: list[float] = []

    def _sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)


@pytest.fixture(name="api")
def api_fixture():
    return _Client(api_user="u@example.com", api_key="k")


@respx.mock
def test_list_users_follows_pages(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v3/users")
    route.side_effect = [
        httpx.Response(
            200, json={"data": [{"id": 1}, {"id": 2}], "paging": _paging(1, 2)}
        ),
        httpx.Response(200, json={"data": [{"id": 3}], "paging": _paging(2, 2)}),
    ]

    result = api.list_users()

    assert [u["id"] for u in result["users"]] == [1, 2, 3]
    assert route.calls[0].request.url.params.get("page") is None
    assert route.calls[1].request.url.params["page"] == "2"


@respx.mock
def test_list_entries_follows_pages_and_keeps_filters(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v2/entries")
    route.side_effect = [
        httpx.Response(
            200, json={"entries": [{"id": 1}, {"id": 2}], "paging": _paging(1, 2)}
        ),
        httpx.Response(200, json={"entries": [{"id": 3}], "paging": _paging(2, 2)}),
    ]

    result = api.list_entries("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", user_id=7)

    assert [e["id"] for e in result["entries"]] == [1, 2, 3]
    second = route.calls[1].request.url.params
    assert second["page"] == "2"
    assert second["filter[users_id]"] == "7"
    assert second["time_since"] == "2026-01-01T00:00:00Z"


@respx.mock
def test_paging_is_capped(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v4/services").mock(
        side_effect=lambda request: httpx.Response(
            200,
            json={
                "data": [{"id": 1}],
                "paging": _paging(int(request.url.params.get("page", 1)), 1000),
            },
        )
    )

    result = api.list_services()

    assert route.call_count == 100
    assert len(result["services"]) == 100


@respx.mock
def test_get_me(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v4/users/me").mock(
        return_value=httpx.Response(200, json={"data": {"id": 5}})
    )

    assert api.get_me() == {"data": {"id": 5}}
    assert route.called


@respx.mock
def test_retries_on_429_then_succeeds(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v2/clock")
    route.side_effect = [
        httpx.Response(429),
        httpx.Response(503),
        httpx.Response(200, json={"running": None}),
    ]

    assert api.get_clock() == {"running": None}
    assert route.call_count == 3
    assert api.sleeps == [0.5, 1.0]


@respx.mock
def test_retry_honours_retry_after_capped(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v2/clock")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "3"}),
        httpx.Response(429, headers={"Retry-After": "120"}),
        httpx.Response(200, json={}),
    ]

    api.get_clock()

    assert api.sleeps == [3.0, 10.0]


@respx.mock
def test_retry_gives_up_after_three_retries(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v2/clock").mock(
        return_value=httpx.Response(429)
    )

    with pytest.raises(httpx.HTTPStatusError):
        api.get_clock()

    assert route.call_count == 4
    assert api.sleeps == [0.5, 1.0, 2.0]


@respx.mock
def test_retries_on_transport_error(api):
    route = respx.delete(f"{DEFAULT_BASE_URL}v2/entries/1")
    route.side_effect = [
        httpx.ConnectError("boom"),
        httpx.Response(200, json={"ok": 1}),
    ]

    assert api.delete_entry(1) == {"ok": 1}
    assert route.call_count == 2


@respx.mock
def test_post_is_never_retried(api):
    route = respx.post(f"{DEFAULT_BASE_URL}v2/clock").mock(
        return_value=httpx.Response(429)
    )

    with pytest.raises(httpx.HTTPStatusError):
        api.clock_start(customers_id=1, services_id=2)

    assert route.call_count == 1
    assert api.sleeps == []


@respx.mock
def test_post_transport_error_not_retried(api):
    route = respx.post(f"{DEFAULT_BASE_URL}v2/clock").mock(
        side_effect=httpx.ConnectError("x")
    )

    with pytest.raises(httpx.ConnectError):
        api.clock_start(customers_id=1, services_id=2)

    assert route.call_count == 1


@respx.mock
def test_non_retryable_status_is_not_retried(api):
    route = respx.get(f"{DEFAULT_BASE_URL}v2/clock").mock(
        return_value=httpx.Response(500)
    )

    with pytest.raises(httpx.HTTPStatusError):
        api.get_clock()

    assert route.call_count == 1


def test_shared_http_client_is_reused(api):
    assert api.http is api.http
    first = api.http
    api.close()
    assert first.is_closed
    assert api.http is not first


@respx.mock
def test_get_user_reports_error_includes_details(api):
    respx.get(f"{DEFAULT_BASE_URL}userreports").mock(
        return_value=httpx.Response(403, json={"error": {"message": "Forbidden thing"}})
    )

    with pytest.raises(httpx.HTTPStatusError, match="Forbidden thing"):
        api.get_user_reports(2026)
