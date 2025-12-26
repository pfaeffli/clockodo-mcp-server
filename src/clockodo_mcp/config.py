"""Configuration for Clockodo MCP Server feature flags and permissions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class FeatureGroup(str, Enum):
    """Available feature groups that can be enabled/disabled."""

    # HR Analytics (Read-only)
    HR_READONLY = "hr_readonly"

    # User operations (current user only)
    USER_READ = "user_read"
    USER_EDIT = "user_edit"

    # Admin operations (all users)
    ADMIN_READ = "admin_read"
    ADMIN_EDIT = "admin_edit"


@dataclass
class ServerConfig:
    """
    Configuration for MCP server features.

    Features can be enabled via environment variables:
    - CLOCKODO_MCP_ENABLE_HR_READONLY=true
    - CLOCKODO_MCP_ENABLE_USER_READ=true
    - CLOCKODO_MCP_ENABLE_USER_EDIT=true
    - CLOCKODO_MCP_ENABLE_ADMIN_READ=true
    - CLOCKODO_MCP_ENABLE_ADMIN_EDIT=true

    Or use presets:
    - CLOCKODO_MCP_PRESET=readonly (only HR analytics)
    - CLOCKODO_MCP_PRESET=user (HR + user read/edit)
    - CLOCKODO_MCP_PRESET=admin (all features enabled)
    """

    hr_readonly: bool = True
    user_read: bool = False
    user_edit: bool = False
    admin_read: bool = False
    admin_edit: bool = False

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """
        Create configuration from environment variables.

        Checks for CLOCKODO_MCP_PRESET first, then individual flags.
        """
        preset = os.getenv("CLOCKODO_MCP_PRESET", "").lower()

        # Apply presets
        if preset == "readonly":
            return cls(
                hr_readonly=True,
                user_read=False,
                user_edit=False,
                admin_read=False,
                admin_edit=False,
            )
        if preset == "user":
            return cls(
                hr_readonly=True,
                user_read=True,
                user_edit=True,
                admin_read=False,
                admin_edit=False,
            )
        if preset == "admin":
            return cls(
                hr_readonly=True,
                user_read=True,
                user_edit=True,
                admin_read=True,
                admin_edit=True,
            )

        # No preset, check individual flags
        def get_bool(key: str, default: bool = False) -> bool:
            value = os.getenv(key, "").lower()
            if value in ("true", "1", "yes", "on"):
                return True
            if value in ("false", "0", "no", "off"):
                return False
            return default

        return cls(
            hr_readonly=get_bool("CLOCKODO_MCP_ENABLE_HR_READONLY", True),
            user_read=get_bool("CLOCKODO_MCP_ENABLE_USER_READ", False),
            user_edit=get_bool("CLOCKODO_MCP_ENABLE_USER_EDIT", False),
            admin_read=get_bool("CLOCKODO_MCP_ENABLE_ADMIN_READ", False),
            admin_edit=get_bool("CLOCKODO_MCP_ENABLE_ADMIN_EDIT", False),
        )

    def is_enabled(self, feature: FeatureGroup) -> bool:
        """Check if a feature group is enabled."""
        feature_map = {
            FeatureGroup.HR_READONLY: self.hr_readonly,
            FeatureGroup.USER_READ: self.user_read,
            FeatureGroup.USER_EDIT: self.user_edit,
            FeatureGroup.ADMIN_READ: self.admin_read,
            FeatureGroup.ADMIN_EDIT: self.admin_edit,
        }
        return feature_map.get(feature, False)

    def get_enabled_features(self) -> list[str]:
        """Get list of enabled feature names."""
        enabled = []
        if self.hr_readonly:
            enabled.append("HR Analytics (Read-only)")
        if self.user_read:
            enabled.append("User Time Entries (Read)")
        if self.user_edit:
            enabled.append("User Time Entries (Edit)")
        if self.admin_read:
            enabled.append("Admin - Read All Users")
        if self.admin_edit:
            enabled.append("Admin - Edit All Users")
        return enabled
