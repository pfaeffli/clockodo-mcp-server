from clockodo_mcp.client import ClockodoClient


def test_client_normalization_v2():
    client = ClockodoClient(
        api_user="u", api_key="k", base_url="https://my.clockodo.com/api/v2/"
    )
    assert client.base_url == "https://my.clockodo.com/api/"


def test_client_normalization_v3():
    client = ClockodoClient(
        api_user="u", api_key="k", base_url="https://my.clockodo.com/api/v3"
    )
    assert client.base_url == "https://my.clockodo.com/api/"


def test_client_normalization_no_version():
    client = ClockodoClient(
        api_user="u", api_key="k", base_url="https://my.clockodo.com/api/"
    )
    assert client.base_url == "https://my.clockodo.com/api/"


def test_client_normalization_no_trailing_slash():
    client = ClockodoClient(
        api_user="u", api_key="k", base_url="https://my.clockodo.com/api"
    )
    assert client.base_url == "https://my.clockodo.com/api/"
