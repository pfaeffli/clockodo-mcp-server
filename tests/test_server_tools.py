from unittest.mock import Mock

from clockodo_mcp.server import create_server


def test_server_list_users_tool_calls_client():
    mock_client = Mock()
    mock_client.list_users.return_value = {"users": [{"id": 1}]}

    server = create_server(client=mock_client)

    # call the tool
    result = server.tools["list_users"]()

    mock_client.list_users.assert_called_once_with()
    assert result["users"][0]["id"] == 1
