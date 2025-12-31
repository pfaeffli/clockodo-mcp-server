"""Tests for role-based configuration."""

import os
from unittest.mock import patch

from clockodo_mcp.config import ServerConfig


def test_role_employee():
    """Test employee role configuration."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "employee"}, clear=True):
        config = ServerConfig.from_env()

        assert config.user_read is True
        assert config.user_edit is True
        assert config.hr_readonly is False
        assert config.team_leader is False
        assert config.admin_read is False
        assert config.admin_edit is False
        assert config.get_role_name() == "employee"


def test_role_team_leader():
    """Test team_leader role configuration."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "team_leader"}, clear=True):
        config = ServerConfig.from_env()

        assert config.user_read is True
        assert config.user_edit is True
        assert config.hr_readonly is False
        assert config.team_leader is True
        assert config.admin_read is False
        assert config.admin_edit is False
        assert config.get_role_name() == "team_leader"


def test_role_hr_analytics():
    """Test hr_analytics role configuration."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "hr_analytics"}, clear=True):
        config = ServerConfig.from_env()

        assert config.user_read is False
        assert config.user_edit is False
        assert config.hr_readonly is True
        assert config.team_leader is False
        assert config.admin_read is False
        assert config.admin_edit is False
        assert config.get_role_name() == "hr_analytics"


def test_role_admin():
    """Test admin role configuration."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "admin"}, clear=True):
        config = ServerConfig.from_env()

        assert config.user_read is True
        assert config.user_edit is True
        assert config.hr_readonly is True
        assert config.team_leader is True
        assert config.admin_read is True
        assert config.admin_edit is True
        assert config.get_role_name() == "admin"


def test_role_case_insensitive():
    """Test that role names are case-insensitive."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "EMPLOYEE"}, clear=True):
        config = ServerConfig.from_env()
        assert config.get_role_name() == "employee"

    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "Team_Leader"}, clear=True):
        config = ServerConfig.from_env()
        assert config.get_role_name() == "team_leader"


def test_default_no_role_set():
    """Test default configuration when no role is set."""
    with patch.dict(os.environ, {}, clear=True):
        config = ServerConfig.from_env()

        # Default is employee-like: own time tracking enabled
        assert config.user_read is True
        assert config.user_edit is True
        assert config.hr_readonly is False
        assert config.team_leader is False


def test_legacy_preset_readonly():
    """Test legacy PRESET=readonly still works."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_PRESET": "readonly"}, clear=True):
        config = ServerConfig.from_env()

        assert config.hr_readonly is True
        assert config.user_read is False
        assert config.user_edit is False
        assert config.get_role_name() == "hr_analytics"


def test_legacy_preset_user():
    """Test legacy PRESET=user still works."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_PRESET": "user"}, clear=True):
        config = ServerConfig.from_env()

        assert config.user_read is True
        assert config.user_edit is True
        assert config.hr_readonly is False
        assert config.get_role_name() == "employee"


def test_legacy_individual_flags():
    """Test legacy individual flags still work."""
    with patch.dict(
        os.environ,
        {
            "CLOCKODO_MCP_ENABLE_HR_READONLY": "true",
            "CLOCKODO_MCP_ENABLE_USER_READ": "false",
            "CLOCKODO_MCP_ENABLE_USER_EDIT": "false",
        },
        clear=True,
    ):
        config = ServerConfig.from_env()

        assert config.hr_readonly is True
        assert config.user_read is False
        assert config.user_edit is False


def test_role_priority_over_preset():
    """Test that ROLE takes priority over PRESET."""
    with patch.dict(
        os.environ,
        {"CLOCKODO_MCP_ROLE": "employee", "CLOCKODO_MCP_PRESET": "admin"},
        clear=True,
    ):
        config = ServerConfig.from_env()
        assert config.get_role_name() == "employee"
        assert config.admin_read is False


def test_role_priority_over_flags():
    """Test that ROLE takes priority over individual flags."""
    with patch.dict(
        os.environ,
        {
            "CLOCKODO_MCP_ROLE": "hr_analytics",
            "CLOCKODO_MCP_ENABLE_USER_EDIT": "true",
        },
        clear=True,
    ):
        config = ServerConfig.from_env()
        assert config.get_role_name() == "hr_analytics"
        assert config.user_edit is False  # Role overrides flag


def test_get_enabled_features_employee():
    """Test feature list for employee role."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "employee"}, clear=True):
        config = ServerConfig.from_env()
        features = config.get_enabled_features()
        assert features == ["Role: employee"]


def test_get_enabled_features_hr_analytics():
    """Test feature list for hr_analytics role."""
    with patch.dict(os.environ, {"CLOCKODO_MCP_ROLE": "hr_analytics"}, clear=True):
        config = ServerConfig.from_env()
        features = config.get_enabled_features()
        assert features == ["Role: hr_analytics"]


def test_get_enabled_features_custom():
    """Test feature list for custom configuration."""
    with patch.dict(
        os.environ,
        {
            "CLOCKODO_MCP_ENABLE_HR_READONLY": "true",
            "CLOCKODO_MCP_ENABLE_TEAM_LEADER": "true",
        },
        clear=True,
    ):
        config = ServerConfig.from_env()
        features = config.get_enabled_features()
        assert "HR Analytics" in features
        assert "Team Management" in features
        assert config.get_role_name() == "custom"
