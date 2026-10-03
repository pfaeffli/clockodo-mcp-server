"""Role gate: tests against the REAL registration built by build_server."""

import asyncio

import pytest

from clockodo_mcp.config import ServerConfig
from clockodo_mcp.server import build_server

HR_TOOLS = {"check_overtime_compliance", "check_vacation_compliance", "get_hr_summary"}
USER_READ_TOOLS = {"get_my_clock", "get_my_time_entries", "get_my_absences"}
USER_EDIT_TOOLS = {
    "start_my_clock",
    "stop_my_clock",
    "add_my_vacation",
    "add_my_sick_day",
    "edit_my_vacation",
    "add_my_time_entry",
    "edit_my_time_entry",
    "delete_my_time_entry",
    "delete_my_vacation",
}
TEAM_TOOLS = {
    "list_pending_vacation_requests",
    "approve_vacation_request",
    "reject_vacation_request",
    "adjust_vacation_dates",
    "create_team_member_vacation",
    "edit_team_member_entry",
    "delete_team_member_entry",
}
MASTER_DATA_TOOLS = {"list_customers", "list_projects", "list_services"}
EMPLOYEE_TOOLS = {"health"} | MASTER_DATA_TOOLS | USER_READ_TOOLS | USER_EDIT_TOOLS
TEAM_LEADER_TOOLS = EMPLOYEE_TOOLS | TEAM_TOOLS | {"list_users"}
HR_ANALYTICS_TOOLS = {"health", "list_users"} | HR_TOOLS
# admin_edit adds no tools (the placeholders were removed)
ADMIN_TOOLS = TEAM_LEADER_TOOLS | HR_TOOLS | {"get_raw_user_reports"}

ALL_RESOURCES = {
    "clockodo://current-entry",
    "clockodo://recent-entries",
    "clockodo://customers",
    "clockodo://services",
    "clockodo://projects",
}
PROMPTS = {"start_tracking", "stop_tracking", "request_vacation"}

EMPLOYEE = {"user_read": True, "user_edit": True}
TEAM_LEADER = {**EMPLOYEE, "team_leader": True}
HR_ANALYTICS = {"hr_readonly": True}
ADMIN = {
    **TEAM_LEADER,
    "hr_readonly": True,
    "admin_read": True,
    "admin_edit": True,
}
CONFIGS = {
    "default": ({}, {"health"}, set(), set()),
    "employee": (EMPLOYEE, EMPLOYEE_TOOLS, ALL_RESOURCES, PROMPTS),
    "team_leader": (TEAM_LEADER, TEAM_LEADER_TOOLS, ALL_RESOURCES, PROMPTS),
    "hr_analytics": (HR_ANALYTICS, HR_ANALYTICS_TOOLS, set(), set()),
    "admin": (ADMIN, ADMIN_TOOLS, ALL_RESOURCES, PROMPTS),
}


def _names(items, attr="name"):
    return {str(getattr(item, attr)) for item in items}


def _registration(flags):
    srv = build_server(ServerConfig(**flags))
    return (
        asyncio.run(srv.list_tools()),
        asyncio.run(srv.list_resources()),
        asyncio.run(srv.list_prompts()),
    )


@pytest.mark.parametrize("role", CONFIGS)
def test_registration_matches_role_exactly(role):
    flags, tools, resources, prompts = CONFIGS[role]
    listed_tools, listed_resources, listed_prompts = _registration(flags)
    assert _names(listed_tools) == tools
    assert _names(listed_resources, "uri") == resources
    assert _names(listed_prompts) == prompts


def test_employee_cannot_see_other_users_or_debug_reports():
    tools = _names(_registration(EMPLOYEE)[0])
    assert "list_users" not in tools
    assert "get_raw_user_reports" not in tools


def test_admin_placeholders_are_gone():
    tools = _names(_registration(ADMIN)[0])
    assert "get_all_time_entries" not in tools
    assert "edit_user_time_entry" not in tools


def test_resources_hidden_without_user_read():
    _, resources, _ = _registration({"user_edit": True})
    assert _names(resources, "uri") == {
        "clockodo://customers",
        "clockodo://services",
        "clockodo://projects",
    }


READ_TOOLS = (
    {"health", "list_users", "list_customers", "list_projects", "list_services"}
    | {"get_raw_user_reports", "list_pending_vacation_requests"}
    | HR_TOOLS
    | USER_READ_TOOLS
)
DESTRUCTIVE_PREFIXES = ("delete_", "edit_", "approve_", "reject_", "adjust_")


def test_every_tool_is_annotated():
    tools = _registration(ADMIN)[0]
    assert tools
    for tool in tools:
        ann = tool.annotations
        assert ann is not None, tool.name
        if tool.name in READ_TOOLS:
            assert ann.read_only_hint is True, tool.name
        else:
            assert ann.read_only_hint is False, tool.name
            assert ann.destructive_hint is not None, tool.name
            expected = tool.name.startswith(DESTRUCTIVE_PREFIXES)
            assert ann.destructive_hint is expected, tool.name


@pytest.mark.parametrize(
    "name",
    [
        "get_my_clock",
        "get_my_time_entries",
        "get_my_absences",
        "list_pending_vacation_requests",
    ],
)
def test_free_text_tools_warn_about_untrusted_data(name):
    tools = {t.name: t for t in _registration(TEAM_LEADER)[0]}
    assert "not instructions" in " ".join(tools[name].description.split())


def test_health_reports_role():
    srv = build_server(ServerConfig(**EMPLOYEE))
    result = asyncio.run(srv.call_tool("health", {}))
    assert "employee" in str(result)
