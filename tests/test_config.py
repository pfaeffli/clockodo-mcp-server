from clockodo_mcp.config import FeatureGroup, ServerConfig


def test_default_config_has_only_hr_readonly():
    config = ServerConfig()
    assert config.hr_readonly is True
    assert config.user_read is False
    assert config.user_edit is False
    assert config.admin_read is False
    assert config.admin_edit is False


def test_config_from_env_readonly_preset(monkeypatch):
    monkeypatch.setenv("CLOCKODO_MCP_PRESET", "readonly")
    config = ServerConfig.from_env()

    assert config.hr_readonly is True
    assert config.user_read is False
    assert config.user_edit is False
    assert config.admin_read is False
    assert config.admin_edit is False


def test_config_from_env_user_preset(monkeypatch):
    monkeypatch.setenv("CLOCKODO_MCP_PRESET", "user")
    config = ServerConfig.from_env()

    assert config.hr_readonly is True
    assert config.user_read is True
    assert config.user_edit is True
    assert config.admin_read is False
    assert config.admin_edit is False


def test_config_from_env_admin_preset(monkeypatch):
    monkeypatch.setenv("CLOCKODO_MCP_PRESET", "admin")
    config = ServerConfig.from_env()

    assert config.hr_readonly is True
    assert config.user_read is True
    assert config.user_edit is True
    assert config.admin_read is True
    assert config.admin_edit is True


def test_config_from_env_individual_flags(monkeypatch):
    monkeypatch.setenv("CLOCKODO_MCP_ENABLE_HR_READONLY", "true")
    monkeypatch.setenv("CLOCKODO_MCP_ENABLE_USER_READ", "true")
    monkeypatch.setenv("CLOCKODO_MCP_ENABLE_USER_EDIT", "false")

    config = ServerConfig.from_env()

    assert config.hr_readonly is True
    assert config.user_read is True
    assert config.user_edit is False
    assert config.admin_read is False
    assert config.admin_edit is False


def test_config_is_enabled():
    config = ServerConfig(hr_readonly=True, user_read=True, user_edit=False)

    assert config.is_enabled(FeatureGroup.HR_READONLY) is True
    assert config.is_enabled(FeatureGroup.USER_READ) is True
    assert config.is_enabled(FeatureGroup.USER_EDIT) is False
    assert config.is_enabled(FeatureGroup.ADMIN_READ) is False
    assert config.is_enabled(FeatureGroup.ADMIN_EDIT) is False


def test_config_get_enabled_features():
    config = ServerConfig(hr_readonly=True, user_read=True, user_edit=True)

    enabled = config.get_enabled_features()

    assert "HR Analytics (Read-only)" in enabled
    assert "User Time Entries (Read)" in enabled
    assert "User Time Entries (Edit)" in enabled
    assert len(enabled) == 3


def test_config_env_boolean_parsing(monkeypatch):
    monkeypatch.setenv("CLOCKODO_MCP_ENABLE_USER_READ", "1")
    monkeypatch.setenv("CLOCKODO_MCP_ENABLE_USER_EDIT", "yes")
    monkeypatch.setenv("CLOCKODO_MCP_ENABLE_ADMIN_READ", "on")

    config = ServerConfig.from_env()

    assert config.user_read is True
    assert config.user_edit is True
    assert config.admin_read is True
