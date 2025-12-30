from clockodo_mcp.server import create_server
from clockodo_mcp.config import ServerConfig


def test_server_has_health_tool():
    server = create_server()
    assert hasattr(server, "tool_names")
    assert "health" in set(server.tool_names)


def test_server_all_features_enabled():
    """Test server with all features enabled."""
    config = ServerConfig(
        hr_readonly=True,
        user_read=True,
        user_edit=True,
        admin_read=True,
        admin_edit=True,
    )
    server = create_server(test_config=config)

    # Base tools
    assert "health" in server.tool_names
    assert "list_users" in server.tool_names
    assert "list_customers" in server.tool_names
    assert "list_services" in server.tool_names

    # HR tools
    assert "check_overtime_compliance" in server.tool_names
    assert "check_vacation_compliance" in server.tool_names
    assert "get_hr_summary" in server.tool_names

    # User read tools
    assert "get_my_time_entries" in server.tool_names

    # User edit tools
    assert "add_my_time_entry" in server.tool_names
    assert "delete_my_vacation" in server.tool_names

    # Admin tools
    assert "get_all_time_entries" in server.tool_names
    assert "edit_user_time_entry" in server.tool_names


def test_server_no_optional_features():
    """Test server with all optional features disabled."""
    config = ServerConfig(
        hr_readonly=False,
        user_read=False,
        user_edit=False,
        admin_read=False,
        admin_edit=False,
    )
    server = create_server(test_config=config)

    # Base tools only
    assert "health" in server.tool_names
    assert "list_users" in server.tool_names

    # No HR tools
    assert "check_overtime_compliance" not in server.tool_names
    assert "check_vacation_compliance" not in server.tool_names

    # No user tools
    assert "get_my_time_entries" not in server.tool_names
    assert "add_my_time_entry" not in server.tool_names

    # No admin tools
    assert "get_all_time_entries" not in server.tool_names
    assert "edit_user_time_entry" not in server.tool_names


def test_server_hr_tools_only():
    """Test server with only HR tools enabled."""
    config = ServerConfig(
        hr_readonly=True,
        user_read=False,
        user_edit=False,
        admin_read=False,
        admin_edit=False,
    )
    server = create_server(test_config=config)

    # HR tools should be present
    assert "check_overtime_compliance" in server.tool_names
    assert "check_vacation_compliance" in server.tool_names
    assert "get_hr_summary" in server.tool_names

    # User tools should be absent
    assert "get_my_time_entries" not in server.tool_names
    assert "add_my_time_entry" not in server.tool_names


def test_server_user_read_only():
    """Test server with only user read tools enabled."""
    config = ServerConfig(
        hr_readonly=False,
        user_read=True,
        user_edit=False,
        admin_read=False,
        admin_edit=False,
    )
    server = create_server(test_config=config)

    # User read tools present
    assert "get_my_time_entries" in server.tool_names

    # User edit tools absent
    assert "add_my_time_entry" not in server.tool_names
    assert "delete_my_vacation" not in server.tool_names


def test_server_user_edit_only():
    """Test server with only user edit tools enabled."""
    config = ServerConfig(
        hr_readonly=False,
        user_read=False,
        user_edit=True,
        admin_read=False,
        admin_edit=False,
    )
    server = create_server(test_config=config)

    # User edit tools present
    assert "add_my_time_entry" in server.tool_names
    assert "delete_my_vacation" in server.tool_names

    # User read tools absent (when edit is enabled but read is not)
    assert "get_my_time_entries" not in server.tool_names


def test_server_admin_read_only():
    """Test server with only admin read tools enabled."""
    config = ServerConfig(
        hr_readonly=False,
        user_read=False,
        user_edit=False,
        admin_read=True,
        admin_edit=False,
    )
    server = create_server(test_config=config)

    # Admin read tools present
    assert "get_all_time_entries" in server.tool_names

    # Admin edit tools absent
    assert "edit_user_time_entry" not in server.tool_names


def test_server_admin_edit_only():
    """Test server with only admin edit tools enabled."""
    config = ServerConfig(
        hr_readonly=False,
        user_read=False,
        user_edit=False,
        admin_read=False,
        admin_edit=True,
    )
    server = create_server(test_config=config)

    # Admin edit tools present
    assert "edit_user_time_entry" in server.tool_names

    # Admin read tools absent
    assert "get_all_time_entries" not in server.tool_names
