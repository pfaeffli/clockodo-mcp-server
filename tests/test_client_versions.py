import httpx
import respx

from clockodo_mcp.client import ClockodoClient


@respx.mock
def test_list_users_v3():
    client = ClockodoClient(api_user="u", api_key="k")
    # Base URL is now .../api/
    route = respx.get("https://my.clockodo.com/api/v3/users").mock(
        return_value=httpx.Response(200, json={"users": []})
    )
    client.list_users()
    assert route.called


@respx.mock
def test_list_customers_v3():
    client = ClockodoClient(api_user="u", api_key="k")
    route = respx.get("https://my.clockodo.com/api/v3/customers").mock(
        return_value=httpx.Response(200, json={"customers": []})
    )
    client.list_customers()
    assert route.called


@respx.mock
def test_list_services_v4_normalized():
    client = ClockodoClient(api_user="u", api_key="k")
    route = respx.get("https://my.clockodo.com/api/v4/services").mock(
        return_value=httpx.Response(200, json={"data": [{"id": 1}]})
    )
    resp = client.list_services()
    assert route.called
    assert "services" in resp
    assert resp["services"][0]["id"] == 1


@respx.mock
def test_list_projects_v4_normalized():
    client = ClockodoClient(api_user="u", api_key="k")
    route = respx.get("https://my.clockodo.com/api/v4/projects").mock(
        return_value=httpx.Response(200, json={"data": [{"id": 1}], "paging": {}})
    )
    resp = client.list_projects()
    assert route.called
    assert "projects" in resp
    assert resp["projects"][0]["id"] == 1


@respx.mock
def test_list_absences_v4_normalized():
    client = ClockodoClient(api_user="u", api_key="k")
    route = respx.get("https://my.clockodo.com/api/v4/absences").mock(
        return_value=httpx.Response(200, json={"data": [{"id": 1}]})
    )
    # Check if it uses filter[year]
    resp = client.list_absences(year=2024)
    assert route.called
    assert "filter[year]" in route.calls[0].request.url.params
    assert route.calls[0].request.url.params["filter[year]"] == "2024"
    assert "absences" in resp
    assert resp["absences"][0]["id"] == 1


@respx.mock
def test_get_clock_v2():
    client = ClockodoClient(api_user="u", api_key="k")
    route = respx.get("https://my.clockodo.com/api/v2/clock").mock(
        return_value=httpx.Response(200, json={"running": None})
    )
    client.get_clock()
    assert route.called
