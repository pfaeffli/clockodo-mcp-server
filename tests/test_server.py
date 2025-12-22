from clockodo_mcp.server import create_server


def test_server_has_health_tool():
    server = create_server()
    assert hasattr(server, "tool_names")
    assert "health" in set(server.tool_names)
