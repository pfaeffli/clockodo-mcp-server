import httpx
import respx
import pytest
from clockodo_mcp.client import DEFAULT_BASE_URL, ClockodoClient


@respx.mock
def test_clock_start():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    # Clockodo API: POST /api/v2/clock
    # Requires billable, customers_id, services_id
    payload = {"customers_id": 123, "services_id": 456, "billable": 1}

    route = respx.post(f"{DEFAULT_BASE_URL}clock").mock(
        return_value=httpx.Response(
            201, json={"running": {"id": 1001, "customers_id": 123}}
        )
    )

    data = client.clock_start(customers_id=123, services_id=456, billable=1)

    assert route.called
    import json

    assert json.loads(route.calls[0].request.content) == payload
    assert data["running"]["id"] == 1001


@respx.mock
def test_clock_stop():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    # Clockodo API: DELETE /api/v2/clock/[ID]
    entry_id = 1001
    route = respx.delete(f"{DEFAULT_BASE_URL}clock/{entry_id}").mock(
        return_value=httpx.Response(200, json={"stopped": {"id": 1001}, "running": None})
    )

    data = client.clock_stop(entry_id)

    assert route.called
    assert data["stopped"]["id"] == 1001


@respx.mock
def test_get_clock():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    route = respx.get(f"{DEFAULT_BASE_URL}clock").mock(
        return_value=httpx.Response(200, json={"running": None})
    )

    data = client.get_clock()

    assert route.called
    assert data["running"] is None


@respx.mock
def test_create_absence():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    payload = {
        "date_since": "2025-01-01",
        "date_until": "2025-01-05",
        "type": 1,  # Vacation
    }

    route = respx.post(f"{DEFAULT_BASE_URL}absences").mock(
        return_value=httpx.Response(201, json={"absence": {"id": 2001}})
    )

    data = client.create_absence(
        date_since="2025-01-01", date_until="2025-01-05", absence_type=1
    )

    assert route.called
    import json

    assert json.loads(route.calls[0].request.content) == {
        "date_since": "2025-01-01",
        "date_until": "2025-01-05",
        "type": 1,
    }
    assert data["absence"]["id"] == 2001


@respx.mock
def test_create_entry():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    payload = {
        "customers_id": 123,
        "services_id": 456,
        "billable": 1,
        "time_since": "2025-12-29T09:00:00Z",
        "time_until": "2025-12-29T17:00:00Z",
    }

    route = respx.post(f"{DEFAULT_BASE_URL}entries").mock(
        return_value=httpx.Response(201, json={"entry": {"id": 3001}})
    )

    data = client.create_entry(
        customers_id=123,
        services_id=456,
        billable=1,
        time_since="2025-12-29T09:00:00Z",
        time_until="2025-12-29T17:00:00Z",
    )

    assert route.called
    assert data["entry"]["id"] == 3001


@respx.mock
def test_list_entries():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    route = respx.get(f"{DEFAULT_BASE_URL}entries").mock(
        return_value=httpx.Response(
            200, json={"entries": [{"id": 3001, "text": "Test entry"}]}
        )
    )

    data = client.list_entries(
        time_since="2025-12-29T00:00:00Z",
        time_until="2025-12-29T23:59:59Z",
        user_id=424873
    )

    assert route.called
    # Verify filter[users_id] parameter is used
    assert route.calls[0].request.url.params.get("filter[users_id]") == "424873"
    assert route.calls[0].request.url.params.get("time_since") == "2025-12-29T00:00:00Z"
    assert data["entries"][0]["id"] == 3001


@respx.mock
def test_edit_absence():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    route = respx.put(f"{DEFAULT_BASE_URL}absences/2001").mock(
        return_value=httpx.Response(200, json={"absence": {"id": 2001, "status": 4}})
    )

    data = client.edit_absence(absence_id=2001, data={"status": 4})

    assert route.called
    import json
    assert json.loads(route.calls[0].request.content) == {"status": 4}
    assert data["absence"]["status"] == 4


@respx.mock
def test_delete_absence():
    client = ClockodoClient(api_user="u@example.com", api_key="k")

    route = respx.delete(f"{DEFAULT_BASE_URL}absences/2001").mock(
        return_value=httpx.Response(200, json={"success": True})
    )

    data = client.delete_absence(absence_id=2001)

    assert route.called
    assert data["success"] is True
