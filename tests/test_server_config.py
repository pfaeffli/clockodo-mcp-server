"""Tests for conditional server tool registration based on configuration."""

from clockodo_mcp.config import ServerConfig
from clockodo_mcp.server import create_server


def test_server_with_readonly_config():
    """Test server only exposes HR readonly tools."""
    config = ServerConfig(hr_readonly=True, user_read=False, user_edit=False)
    server = create_server(test_config=config)

    assert "health" in server.tool_names
    assert "list_users" in server.tool_names
    assert "check_overtime_compliance" in server.tool_names
    assert "check_vacation_compliance" in server.tool_names
    assert "get_hr_summary" in server.tool_names

    # User tools should not be registered
    assert "get_my_time_entries" not in server.tool_names
    assert "add_my_time_entry" not in server.tool_names


def test_server_with_user_preset_config():
    """Test server with user preset (HR + user read/edit)."""
    config = ServerConfig(hr_readonly=True, user_read=True, user_edit=True)
    server = create_server(test_config=config)

    # HR tools
    assert "check_overtime_compliance" in server.tool_names
    assert "get_hr_summary" in server.tool_names

    # User tools
    assert "get_my_time_entries" in server.tool_names
    assert "add_my_time_entry" in server.tool_names

    # Admin tools should not be registered
    assert "get_all_time_entries" not in server.tool_names
    assert "edit_user_time_entry" not in server.tool_names


def test_server_with_admin_preset_config():
    """Test server with admin preset (all features)."""
    config = ServerConfig(
        hr_readonly=True,
        user_read=True,
        user_edit=True,
        admin_read=True,
        admin_edit=True,
    )
    server = create_server(test_config=config)

    # HR tools
    assert "check_overtime_compliance" in server.tool_names

    # User tools
    assert "get_my_time_entries" in server.tool_names
    assert "add_my_time_entry" in server.tool_names

    # Admin tools
    assert "get_all_time_entries" in server.tool_names
    assert "edit_user_time_entry" in server.tool_names


def test_server_with_no_features():
    """Test server with all features disabled (only health + list_users)."""
    config = ServerConfig(
        hr_readonly=False,
        user_read=False,
        user_edit=False,
        admin_read=False,
        admin_edit=False,
    )
    server = create_server(test_config=config)

    # Only core tools
    assert "health" in server.tool_names
    assert "list_users" in server.tool_names

    # No feature tools should be registered
    assert "check_overtime_compliance" not in server.tool_names
    assert "get_my_time_entries" not in server.tool_names
    assert "add_my_time_entry" not in server.tool_names
    assert "get_all_time_entries" not in server.tool_names
    assert "edit_user_time_entry" not in server.tool_names


def test_server_with_only_user_edit():
    """Test server with only user_edit enabled."""
    config = ServerConfig(hr_readonly=False, user_read=False, user_edit=True)
    server = create_server(test_config=config)

    assert "add_my_time_entry" in server.tool_names
    assert "check_overtime_compliance" not in server.tool_names
    assert "get_my_time_entries" not in server.tool_names


def test_server_stores_config():
    """Test that server stores its configuration."""
    config = ServerConfig(hr_readonly=True, user_read=True)
    server = create_server(test_config=config)

    assert server.config.hr_readonly is True
    assert server.config.user_read is True
    assert server.config.user_edit is False
