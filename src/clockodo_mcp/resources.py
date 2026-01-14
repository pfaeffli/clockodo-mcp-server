"""
MCP Resources for Clockodo Server.

Provides resources that allow users to attach and manage context data.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .client import ClockodoClient


def get_current_time_entry_resource() -> dict:
    """
    Get the current running time entry as a resource.

    Returns:
        Dictionary with current time entry data
    """
    client = ClockodoClient.from_env()
    clock = client.get_clock()

    if not clock or "running" not in clock:
        return {
            "uri": "clockodo://current-entry",
            "name": "Current Time Entry",
            "description": "No time entry currently running",
            "mimeType": "application/json",
            "content": {"running": False},
        }

    entry = clock["running"]
    return {
        "uri": "clockodo://current-entry",
        "name": "Current Time Entry",
        "description": f"Currently tracking: {entry.get('customers_name', 'Unknown')} - {entry.get('services_name', 'Unknown')}",
        "mimeType": "application/json",
        "content": entry,
    }


def get_user_profile_resource() -> dict:
    """
    Get the authenticated user's profile as a resource.

    Returns:
        Dictionary with user profile data
    """
    client = ClockodoClient.from_env()
    users = client.list_users()

    # Find the authenticated user (the API returns all users, but we can identify the current user)
    # For now, we'll return basic user info structure
    return {
        "uri": "clockodo://user-profile",
        "name": "User Profile",
        "description": "Authenticated user profile information",
        "mimeType": "application/json",
        "content": {"users_count": len(users.get("users", []))},
    }


def get_customers_resource() -> dict:
    """
    Get the list of customers as a resource.

    Returns:
        Dictionary with customers data
    """
    client = ClockodoClient.from_env()
    customers = client.list_customers()

    customer_list = customers.get("customers", [])
    customer_names = [c.get("name", "Unknown") for c in customer_list]

    return {
        "uri": "clockodo://customers",
        "name": "Customers List",
        "description": f"Available customers ({len(customer_list)} total)",
        "mimeType": "application/json",
        "content": {
            "count": len(customer_list),
            "customers": customer_list,
            "names": customer_names,
        },
    }


def get_services_resource() -> dict:
    """
    Get the list of services as a resource.

    Returns:
        Dictionary with services data
    """
    client = ClockodoClient.from_env()
    services = client.list_services()

    service_list = services.get("services", [])
    service_names = [s.get("name", "Unknown") for s in service_list]

    return {
        "uri": "clockodo://services",
        "name": "Services List",
        "description": f"Available services ({len(service_list)} total)",
        "mimeType": "application/json",
        "content": {
            "count": len(service_list),
            "services": service_list,
            "names": service_names,
        },
    }


def get_projects_resource() -> dict:
    """
    Get the list of projects as a resource.

    Returns:
        Dictionary with projects data
    """
    client = ClockodoClient.from_env()
    projects = client.list_projects()

    project_list = projects.get("projects", [])
    project_names = [p.get("name", "Unknown") for p in project_list]

    return {
        "uri": "clockodo://projects",
        "name": "Projects List",
        "description": f"Available projects ({len(project_list)} total)",
        "mimeType": "application/json",
        "content": {
            "count": len(project_list),
            "projects": project_list,
            "names": project_names,
        },
    }


def get_recent_entries_resource(days: int = 7) -> dict:
    """
    Get recent time entries as a resource.

    Args:
        days: Number of days to look back (default: 7)

    Returns:
        Dictionary with recent entries data
    """
    client = ClockodoClient.from_env()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    time_since = start_date.strftime("%Y-%m-%d 00:00:00")
    time_until = end_date.strftime("%Y-%m-%d 23:59:59")

    entries = client.list_entries(time_since=time_since, time_until=time_until)
    entry_list = entries.get("entries", [])

    return {
        "uri": f"clockodo://recent-entries?days={days}",
        "name": f"Recent Time Entries (Last {days} Days)",
        "description": f"Time entries from the last {days} days ({len(entry_list)} entries)",
        "mimeType": "application/json",
        "content": {
            "count": len(entry_list),
            "entries": entry_list,
            "period": {"start": time_since, "end": time_until},
        },
    }
