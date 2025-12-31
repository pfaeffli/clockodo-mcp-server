from unittest.mock import Mock
from clockodo_mcp.tools.team_leader_tools import register_team_leader_tools


def test_register_team_leader_tools():
    mock_mcp = Mock()
    mock_service = Mock()

    # Track registered tools
    registered_tools = {}

    def tool_decorator():
        def wrapper(func):
            registered_tools[func.__name__] = func
            return func

        return wrapper

    mock_mcp.tool.side_effect = tool_decorator

    register_team_leader_tools(mock_mcp, mock_service)

    # Verify all tools are registered
    expected_tools = [
        "list_pending_vacation_requests",
        "approve_vacation_request",
        "reject_vacation_request",
        "adjust_vacation_dates",
        "create_team_member_vacation",
        "edit_team_member_entry",
        "delete_team_member_entry",
    ]

    for tool_name in expected_tools:
        assert tool_name in registered_tools

    # Test list_pending_vacation_requests
    mock_service.list_pending_vacations.return_value = [{"id": 1}]
    result = registered_tools["list_pending_vacation_requests"](year=2024)
    mock_service.list_pending_vacations.assert_called_once_with(2024)
    assert result == [{"id": 1}]

    # Test approve_vacation_request
    mock_service.approve_vacation.return_value = {"status": 1}
    result = registered_tools["approve_vacation_request"](absence_id=123)
    mock_service.approve_vacation.assert_called_once_with(123)
    assert result == {"status": 1}

    # Test reject_vacation_request
    mock_service.reject_vacation.return_value = {"status": 2}
    result = registered_tools["reject_vacation_request"](absence_id=124)
    mock_service.reject_vacation.assert_called_once_with(124)
    assert result == {"status": 2}

    # Test adjust_vacation_dates
    mock_service.adjust_vacation_length.return_value = {"id": 125}
    result = registered_tools["adjust_vacation_dates"](125, "2024-01-01", "2024-01-05")
    mock_service.adjust_vacation_length.assert_called_once_with(
        125, "2024-01-01", "2024-01-05"
    )
    assert result == {"id": 125}

    # Test create_team_member_vacation
    mock_service.create_team_vacation.return_value = {"id": 126}
    result = registered_tools["create_team_member_vacation"](
        user_id=42, date_since="2024-02-01", date_until="2024-02-05"
    )
    mock_service.create_team_vacation.assert_called_once_with(
        user_id=42,
        date_since="2024-02-01",
        date_until="2024-02-05",
        absence_type=1,
        auto_approve=True,
    )
    assert result == {"id": 126}

    # Test edit_team_member_entry
    mock_service.edit_team_entry.return_value = {"id": 100}
    result = registered_tools["edit_team_member_entry"](
        entry_id=100, data={"text": "updated"}
    )
    mock_service.edit_team_entry.assert_called_once_with(100, {"text": "updated"})
    assert result == {"id": 100}

    # Test delete_team_member_entry
    mock_service.delete_team_entry.return_value = {"success": True}
    result = registered_tools["delete_team_member_entry"](entry_id=101)
    mock_service.delete_team_entry.assert_called_once_with(101)
    assert result == {"success": True}
