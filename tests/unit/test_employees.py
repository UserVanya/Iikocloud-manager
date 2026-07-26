"""Unit tests for Employees domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    ActiveCourierLocationsByTerminalGroupRequest,
    ActiveCourierLocationsResponse,
    ChangePersonalSessionResponse,
    ClosePersonalSessionRequest,
    CourierLocationsByTimeOffsetRequest,
    CourierLocationsByTimeOffsetResponse,
    CouriersAndCheckRoleRequest,
    CouriersRequest,
    EmployeeInfoRequest,
    EmployeeInfoResponse,
    EmployeesResponse,
    EmployeesWithRoleSignResponse,
    GetPersonalSessionInfoRequest,
    GetPersonalSessionInfoResponse,
    GetTerminalGroupsOfEmployeeRequest,
    GetTerminalGroupsOfEmployeeResponse,
    OpenPersonalSessionRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_employees_api"

METHODS: list[tuple[str, object, str, type]] = [
    (
        "get_couriers",
        CouriersRequest(organization_ids=[ORG_ID]),
        "couriers_request",
        EmployeesResponse,
    ),
    (
        "get_couriers_by_role",
        CouriersAndCheckRoleRequest(
            organization_ids=[ORG_ID], roles_to_check=["R"]
        ),
        "couriers_and_check_role_request",
        EmployeesWithRoleSignResponse,
    ),
    (
        "get_employee_info",
        EmployeeInfoRequest(id=ORG_ID, organization_id=ORG_ID),
        "employee_info_request",
        EmployeeInfoResponse,
    ),
    (
        "get_active_courier_locations",
        CouriersRequest(organization_ids=[ORG_ID]),
        "couriers_request",
        ActiveCourierLocationsResponse,
    ),
    (
        "get_active_courier_locations_by_terminal",
        ActiveCourierLocationsByTerminalGroupRequest(
            organization_id=ORG_ID, terminal_group_id=ORG_ID
        ),
        "active_courier_locations_by_terminal_group_request",
        ActiveCourierLocationsResponse,
    ),
    (
        "get_courier_location_history",
        CourierLocationsByTimeOffsetRequest(
            organization_ids=[ORG_ID], offset_in_seconds=60
        ),
        "courier_locations_by_time_offset_request",
        CourierLocationsByTimeOffsetResponse,
    ),
    (
        "get_personal_session_info",
        GetPersonalSessionInfoRequest(
            employee_id=ORG_ID,
            organization_id=ORG_ID,
            terminal_group_id=ORG_ID,
        ),
        "get_personal_session_info_request",
        GetPersonalSessionInfoResponse,
    ),
    (
        "get_terminal_groups_of_employee",
        GetTerminalGroupsOfEmployeeRequest(employee_id=ORG_ID),
        "get_terminal_groups_of_employee_request",
        GetTerminalGroupsOfEmployeeResponse,
    ),
    (
        "open_personal_session",
        OpenPersonalSessionRequest(
            employee_id=ORG_ID,
            organization_id=ORG_ID,
            terminal_group_id=ORG_ID,
        ),
        "open_personal_session_request",
        ChangePersonalSessionResponse,
    ),
    (
        "close_personal_session",
        ClosePersonalSessionRequest(
            employee_id=ORG_ID,
            organization_id=ORG_ID,
            terminal_group_id=ORG_ID,
        ),
        "close_personal_session_request",
        ChangePersonalSessionResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_employees_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 10 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
