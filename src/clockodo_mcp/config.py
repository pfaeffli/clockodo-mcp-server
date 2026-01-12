"""Configuration for Clockodo MCP Server feature flags and permissions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """Available roles for Clockodo MCP server."""

    EMPLOYEE = "employee"
    TEAM_LEADER = "team_leader"
    HR_ANALYTICS = "hr_analytics"
    ADMIN = "admin"


class FeatureGroup(str, Enum):
    """Available feature groups that can be enabled/disabled."""

    # HR Analytics (Read-only)
    HR_READONLY = "hr_readonly"

    # User operations (current user only)
    USER_READ = "user_read"
    USER_EDIT = "user_edit"

    # Team leader operations (team management)
    TEAM_LEADER = "team_leader"

    # Admin operations (all users)
    ADMIN_READ = "admin_read"
    ADMIN_EDIT = "admin_edit"


@dataclass
class ServerConfig:  # pylint: disable=too-many-instance-attributes
    """
    Configuration for MCP server features.

    Primary configuration (recommended):
    - CLOCKODO_MCP_ROLE=employee (default: own time tracking only)
    - CLOCKODO_MCP_ROLE=team_leader (employee + vacation approval & team edits)
    - CLOCKODO_MCP_ROLE=hr_analytics (HR compliance reports only)
    - CLOCKODO_MCP_ROLE=admin (full access)

    Transport configuration:
    - CLOCKODO_MCP_TRANSPORT=stdio (default: stdin/stdout for local processes)
    - CLOCKODO_MCP_TRANSPORT=sse (HTTP/SSE for remote access)
    - CLOCKODO_MCP_PORT=8000 (default port when using SSE transport)

    Legacy configuration (deprecated, but still supported):
    - Individual flags: CLOCKODO_MCP_ENABLE_HR_READONLY=true, etc.
    - Presets: CLOCKODO_MCP_PRESET=readonly, user, team_leader, admin
    """

    hr_readonly: bool = False
    user_read: bool = False
    user_edit: bool = False
    team_leader: bool = False
    admin_read: bool = False
    admin_edit: bool = False
    transport: str = "stdio"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """
        Create configuration from environment variables.

        Priority order:
        1. CLOCKODO_MCP_ROLE (recommended)
        2. CLOCKODO_MCP_PRESET (legacy)
        3. Individual CLOCKODO_MCP_ENABLE_* flags (legacy)
        """
        role = os.getenv("CLOCKODO_MCP_ROLE", "").lower()

        # Apply role-based configuration (primary method)
        # Transport configuration (applies to all roles)
        transport = os.getenv("CLOCKODO_MCP_TRANSPORT", "stdio").lower()
        if transport not in ("stdio", "sse"):
            transport = "stdio"
        port = int(os.getenv("CLOCKODO_MCP_PORT", "8000"))

        role_configs = {
            Role.EMPLOYEE.value: {
                "hr_readonly": False,
                "user_read": True,
                "user_edit": True,
                "team_leader": False,
                "admin_read": False,
                "admin_edit": False,
                "transport": transport,
                "port": port,
            },
            Role.TEAM_LEADER.value: {
                "hr_readonly": False,
                "user_read": True,
                "user_edit": True,
                "team_leader": True,
                "admin_read": False,
                "admin_edit": False,
                "transport": transport,
                "port": port,
            },
            Role.HR_ANALYTICS.value: {
                "hr_readonly": True,
                "user_read": False,
                "user_edit": False,
                "team_leader": False,
                "admin_read": False,
                "admin_edit": False,
                "transport": transport,
                "port": port,
            },
            Role.ADMIN.value: {
                "hr_readonly": True,
                "user_read": True,
                "user_edit": True,
                "team_leader": True,
                "admin_read": True,
                "admin_edit": True,
                "transport": transport,
                "port": port,
            },
        }

        if role in role_configs:
            return cls(**role_configs[role])  # type: ignore[arg-type]

        # Legacy preset support
        preset = os.getenv("CLOCKODO_MCP_PRESET", "").lower()
        preset_configs = {
            "readonly": {
                "hr_readonly": True,
                "user_read": False,
                "user_edit": False,
                "team_leader": False,
                "admin_read": False,
                "admin_edit": False,
                "transport": transport,
                "port": port,
            },
            "user": {
                "hr_readonly": False,
                "user_read": True,
                "user_edit": True,
                "team_leader": False,
                "admin_read": False,
                "admin_edit": False,
                "transport": transport,
                "port": port,
            },
            "team_leader": {
                "hr_readonly": False,
                "user_read": True,
                "user_edit": True,
                "team_leader": True,
                "admin_read": False,
                "admin_edit": False,
                "transport": transport,
                "port": port,
            },
            "admin": {
                "hr_readonly": True,
                "user_read": True,
                "user_edit": True,
                "team_leader": True,
                "admin_read": True,
                "admin_edit": True,
                "transport": transport,
                "port": port,
            },
        }

        if preset in preset_configs:
            return cls(**preset_configs[preset])  # type: ignore[arg-type]

        # Legacy individual flags support
        def get_bool(key: str, default: bool = False) -> bool:
            value = os.getenv(key, "").lower()
            if value in ("true", "1", "yes", "on"):
                return True
            if value in ("false", "0", "no", "off"):
                return False
            return default

        return cls(
            hr_readonly=get_bool("CLOCKODO_MCP_ENABLE_HR_READONLY", False),
            user_read=get_bool("CLOCKODO_MCP_ENABLE_USER_READ", True),
            user_edit=get_bool("CLOCKODO_MCP_ENABLE_USER_EDIT", True),
            team_leader=get_bool("CLOCKODO_MCP_ENABLE_TEAM_LEADER", False),
            admin_read=get_bool("CLOCKODO_MCP_ENABLE_ADMIN_READ", False),
            admin_edit=get_bool("CLOCKODO_MCP_ENABLE_ADMIN_EDIT", False),
            transport=transport,
            port=port,
        )

    def is_enabled(self, feature: FeatureGroup) -> bool:
        """Check if a feature group is enabled."""
        feature_map = {
            FeatureGroup.HR_READONLY: self.hr_readonly,
            FeatureGroup.USER_READ: self.user_read,
            FeatureGroup.USER_EDIT: self.user_edit,
            FeatureGroup.TEAM_LEADER: self.team_leader,
            FeatureGroup.ADMIN_READ: self.admin_read,
            FeatureGroup.ADMIN_EDIT: self.admin_edit,
        }
        return feature_map.get(feature, False)

    def get_role_name(self) -> str:
        """Get the role name based on enabled features."""
        is_admin = (
            self.hr_readonly
            and self.user_read
            and self.user_edit
            and self.team_leader
            and self.admin_read
            and self.admin_edit
        )
        if is_admin:
            return "admin"

        is_team_leader = (
            self.user_read
            and self.user_edit
            and self.team_leader
            and not self.hr_readonly
        )
        if is_team_leader:
            return "team_leader"

        if self.hr_readonly and not self.user_read and not self.team_leader:
            return "hr_analytics"

        is_employee = (
            self.user_read
            and self.user_edit
            and not self.hr_readonly
            and not self.team_leader
        )
        if is_employee:
            return "employee"
        return "custom"

    def get_enabled_features(self) -> list[str]:
        """Get list of enabled feature names."""
        role = self.get_role_name()
        if role != "custom":
            return [f"Role: {role}"]

        # For custom configurations, list individual features
        enabled = []
        if self.hr_readonly:
            enabled.append("HR Analytics")
        if self.user_read and self.user_edit:
            enabled.append("Own Time Tracking")
        elif self.user_read:
            enabled.append("Own Time Tracking (Read-only)")
        if self.team_leader:
            enabled.append("Team Management")
        if self.admin_read or self.admin_edit:
            enabled.append("Admin Access")
        return enabled if enabled else ["No features enabled"]
