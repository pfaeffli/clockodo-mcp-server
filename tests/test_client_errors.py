"""Error-path tests for ClockodoClient._request (#58)."""

import logging

import httpx
import pytest
import respx

from clockodo_mcp.client import DEFAULT_BASE_URL, MAX_ERROR_DETAIL, ClockodoClient

URL = f"{DEFAULT_BASE_URL}v4/users/me"


class _Client(ClockodoClient):
    """Client that does not sleep between retries."""

    def _sleep(self, seconds: float) -> None:
        pass


@pytest.fixture(name="api")
def api_fixture():
    return _Client(api_user="u@example.com", api_key="k")


@pytest.mark.parametrize(
    "status,body",
    [
        (401, {"error": {"message": "bad credentials"}}),
        (403, {"error": {"message": "forbidden"}}),
        (404, {"error": {"message": "not found"}}),
        (422, {"error": {"message": "invalid", "fields": ["time_since"]}}),
    ],
)
@respx.mock
def test_client_errors_include_json_details(api, status, body):
    route = respx.get(URL).respond(status, json=body)

    with pytest.raises(httpx.HTTPStatusError) as exc:
        api.get_me()

    assert exc.value.response.status_code == status
    assert body["error"]["message"] in str(exc.value)
    assert "Details:" in str(exc.value)
    assert route.call_count == 1


@respx.mock
def test_500_non_json_body_raises_original_error(api):
    respx.get(URL).respond(500, text="<html>boom</html>")

    with pytest.raises(httpx.HTTPStatusError) as exc:
        api.get_me()

    assert exc.value.response.status_code == 500
    assert "Details:" not in str(exc.value)


@respx.mock
def test_timeout_raises_after_retries(api):
    route = respx.get(URL).mock(side_effect=httpx.ReadTimeout("slow"))

    with pytest.raises(httpx.ReadTimeout):
        api.get_me()

    assert route.call_count > 1


@respx.mock
def test_error_details_are_truncated_and_logged_as_warning(api, caplog):
    respx.get(URL).respond(422, json={"error": "x" * 5000})

    with caplog.at_level(logging.DEBUG, logger="clockodo_mcp.client"):
        with pytest.raises(httpx.HTTPStatusError) as exc:
            api.get_me()

    message = str(exc.value)
    assert "{'error': 'xxx" in message
    assert len(message) < MAX_ERROR_DETAIL + 300
    assert message.endswith("...[truncated]")
    records = [r for r in caplog.records if "API Error" in r.getMessage()]
    assert records
    assert all(r.levelno == logging.WARNING for r in records)
