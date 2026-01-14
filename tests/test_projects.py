import httpx
import respx

from clockodo_mcp.client import DEFAULT_BASE_URL, ClockodoClient


@respx.mock
def test_list_projects_calls_clockodo_and_returns_json():
    client = ClockodoClient(api_user="u@example.com", api_key="k", user_agent="ua")

    route = respx.get(f"{DEFAULT_BASE_URL}v4/projects").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": 300, "name": "Project Alpha"}]}
        )
    )

    # Once implemented, it should work:
    data = client.list_projects()
    assert route.called
    assert data["projects"][0]["name"] == "Project Alpha"
