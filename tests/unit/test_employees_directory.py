"""Unit tests: справочник сотрудников, должности, явки и помощники раздела (0.5.0)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    AttendanceCreateRequest,
    AttendanceCreateResponse,
    AttendanceDeleteRequest,
    AttendanceDeleteResponse,
    AttendanceListRequest,
    AttendanceListResponse,
    AttendanceResponse,
    AttendanceTypeListRequest,
    AttendanceTypeListResponse,
    AttendanceUpdateRequest,
    AttendanceUpdateResponse,
    EmployeeCreateRequest,
    EmployeeDirectoryEntry,
    EmployeeFireRequest,
    EmployeeFireResponse,
    EmployeeGetRequest,
    EmployeePositionResponse,
    EmployeeResponse,
    EmployeeRestoreRequest,
    EmployeeRestoreResponse,
    EmployeesFilter,
    EmployeesResponse,
    EmployeeUpdateRequest,
    GetPersonalSessionInfoResponse,
    GetPositionRequest,
    ListPositionsRequest,
    ListPositionsResponse,
    RmsEmployeeItemsResponse,
    SwaggerEmployeeListResponse,
)

from iikocloud import EMPLOYEE_CONTACT_FIELDS
from iikocloud.mixins._base import ApiMethod
from tests.unit.conftest import manager_with_stub_api, manager_with_stub_token

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
EMP_ID = UUID("22345678-1234-1234-1234-123456789abc")
TG_ID = UUID("32345678-1234-1234-1234-123456789abc")
START = "2026-10-01T00:00:00Z"
END = "2026-10-02T00:00:00Z"

DIRECTORY_METHODS: list[tuple[str, object, str, type]] = [
    (
        "get_employee",
        EmployeeGetRequest(id=str(EMP_ID)),
        "employee_get_request",
        EmployeeResponse,
    ),
    (
        "create_employee",
        EmployeeCreateRequest(code="1", name="n", main_organization_id=str(ORG_ID)),
        "employee_create_request",
        EmployeeResponse,
    ),
    (
        "update_employee",
        EmployeeUpdateRequest(id=str(EMP_ID), phone="+70000000000"),
        "employee_update_request",
        EmployeeResponse,
    ),
    (
        "fire_employees",
        EmployeeFireRequest(ids=[str(EMP_ID)]),
        "employee_fire_request",
        EmployeeFireResponse,
    ),
    (
        "restore_employee",
        EmployeeRestoreRequest(id=str(EMP_ID)),
        "employee_restore_request",
        EmployeeRestoreResponse,
    ),
]

POSITION_METHODS: list[tuple[str, object, str, type]] = [
    (
        "get_employee_position",
        GetPositionRequest(id=str(EMP_ID)),
        "get_position_request",
        EmployeePositionResponse,
    ),
    (
        "list_employee_positions",
        ListPositionsRequest(limit=50),
        "list_positions_request",
        ListPositionsResponse,
    ),
]

ATTENDANCE_METHODS: list[tuple[str, object, str, type]] = [
    (
        "list_employee_attendances",
        AttendanceListRequest(organization_id=ORG_ID, start_at=START, end_at=END),
        "attendance_list_request",
        AttendanceListResponse,
    ),
    (
        "create_employee_attendance",
        AttendanceCreateRequest(
            employee_id=EMP_ID,
            organization_id=ORG_ID,
            role_id=ORG_ID,
            start_at=START,
            end_at=END,
        ),
        "attendance_create_request",
        AttendanceCreateResponse,
    ),
    (
        "update_employee_attendance",
        AttendanceUpdateRequest(
            id=EMP_ID,
            attendance_type_id=ORG_ID,
            employee_id=EMP_ID,
            organization_id=ORG_ID,
            role_id=ORG_ID,
            start_at=START,
            end_at=END,
            is_confirmed_manually=True,
        ),
        "attendance_update_request",
        AttendanceUpdateResponse,
    ),
    (
        "delete_employee_attendance",
        AttendanceDeleteRequest(id=EMP_ID, organization_id=ORG_ID),
        "attendance_delete_request",
        AttendanceDeleteResponse,
    ),
    (
        "list_employee_attendance_types",
        AttendanceTypeListRequest(is_deleted=False),
        "attendance_type_list_request",
        AttendanceTypeListResponse,
    ),
]

CASES = (
    [(*m, "_employees_employees_api") for m in DIRECTORY_METHODS]
    + [(*m, "_employees_positions_api") for m in POSITION_METHODS]
    + [(*m, "_employees_attendance_api") for m in ATTENDANCE_METHODS]
)


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls", "api_slot"), CASES
)
async def test_directory_and_attendance_methods_delegate(
    method_name: str,
    sdk_request: object,
    sdk_kwarg: str,
    response_cls: type,
    api_slot: str,
) -> None:
    """Каждый метод зовёт одноимённый метод SDK своего клиента и отдаёт его ответ."""
    manager, mock_api = await manager_with_stub_api(api_slot)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(("method_name", "_r", "_k", "_c", "_s"), CASES)
async def test_every_new_method_goes_through_its_own_limiter(
    method_name: str, _r: object, _k: str, _c: type, _s: str
) -> None:
    """Предел, повтор после 401 и ошибки — общий execute_with_retry с ApiMethod метода."""
    manager, _ = await manager_with_stub_token()
    calls: list[ApiMethod] = []

    async def fake_execute(method: ApiMethod, api_call: object) -> str:
        calls.append(method)
        return "ok"

    manager.execute_with_retry = fake_execute  # type: ignore[assignment]

    assert await getattr(manager, method_name)(_r) == "ok"
    assert calls == [ApiMethod(method_name)]


def _employee(n: int) -> EmployeeResponse:
    return EmployeeResponse(id=f"e{n}", phone=f"+7900000000{n % 10}")


async def test_list_all_employees_pages_and_asks_for_phone() -> None:
    manager, mock_api = await manager_with_stub_api("_employees_employees_api")
    pages = [
        SwaggerEmployeeListResponse(items=[_employee(1), _employee(2)], total_count=3),
        SwaggerEmployeeListResponse(items=[_employee(3)], total_count=3),
    ]
    mock_api.list_employees = AsyncMock(side_effect=pages)
    only_working = EmployeesFilter(var_field="isFired", value="false")

    result = await manager.list_all_employees(filters=[only_working], page_size=2)

    assert [e.id for e in result] == ["e1", "e2", "e3"]
    first, second = (
        c.kwargs["employee_list_request"] for c in mock_api.list_employees.await_args_list
    )
    assert "phone" in first.fields
    assert first.fields == list(EMPLOYEE_CONTACT_FIELDS)
    assert first.filters == [only_working]
    assert (first.limit, first.offset) == (2, 0)
    assert (second.limit, second.offset) == (2, 2)


async def test_list_all_employees_stops_on_short_page_without_total() -> None:
    manager, mock_api = await manager_with_stub_api("_employees_employees_api")
    mock_api.list_employees = AsyncMock(
        return_value=SwaggerEmployeeListResponse(items=[_employee(1)])
    )

    result = await manager.list_all_employees(page_size=5)

    assert len(result) == 1
    mock_api.list_employees.assert_awaited_once()


async def test_list_all_employee_attendances_pages_by_thousand() -> None:
    manager, mock_api = await manager_with_stub_api("_employees_attendance_api")
    full = [AttendanceResponse(employee_id=EMP_ID) for _ in range(1000)]
    mock_api.list_employee_attendances = AsyncMock(
        side_effect=[
            AttendanceListResponse(items=full, total_count=1001),
            AttendanceListResponse(items=[AttendanceResponse()], total_count=1001),
        ]
    )

    result = await manager.list_all_employee_attendances(
        str(ORG_ID), START, END, employee_ids=[EMP_ID], is_closed=True
    )

    assert len(result) == 1001
    calls = mock_api.list_employee_attendances.await_args_list
    first = calls[0].kwargs["attendance_list_request"]
    assert first.organization_id == ORG_ID
    assert first.employee_ids == [EMP_ID]
    assert first.is_closed is True
    assert (first.start_at, first.end_at) == (START, END)
    assert calls[1].kwargs["attendance_list_request"].offset == 1000


async def test_list_all_employee_attendances_rejects_page_over_iiko_maximum() -> None:
    manager, _ = await manager_with_stub_api("_employees_attendance_api")
    with pytest.raises(ValueError):
        await manager.list_all_employee_attendances(ORG_ID, START, END, page_size=1001)


async def test_list_organization_couriers_flattens_groups() -> None:
    manager, mock_api = await manager_with_stub_api("_employees_api")
    courier = EmployeeDirectoryEntry(id=EMP_ID)
    mock_api.get_couriers = AsyncMock(
        return_value=EmployeesResponse(
            correlation_id=ORG_ID,
            employees=[RmsEmployeeItemsResponse(organization_id=ORG_ID, items=[courier])],
        )
    )

    result = await manager.list_organization_couriers(str(ORG_ID))

    assert result == [courier]
    request = mock_api.get_couriers.await_args.kwargs["couriers_request"]
    assert request.organization_ids == [ORG_ID]


@pytest.mark.parametrize(
    ("opened", "error", "expected"),
    [
        (True, None, True),
        (False, None, False),
        (None, None, False),
        # Стенд, 13.10.2026: успех iiko пишет в поле ошибки словами.
        (True, "NO_ERROR", True),
        (False, "NO_ERROR", False),
    ],
)
async def test_is_personal_session_open(
    opened: bool | None, error: str | None, expected: bool
) -> None:
    manager, mock_api = await manager_with_stub_api("_employees_api")
    mock_api.get_personal_session_info = AsyncMock(
        return_value=GetPersonalSessionInfoResponse(
            correlation_id=ORG_ID, is_session_opened=opened, error=error
        )
    )

    assert await manager.is_personal_session_open(EMP_ID, ORG_ID, TG_ID) is expected
    request = mock_api.get_personal_session_info.await_args.kwargs[
        "get_personal_session_info_request"
    ]
    assert (request.employee_id, request.organization_id, request.terminal_group_id) == (
        EMP_ID,
        ORG_ID,
        TG_ID,
    )


async def test_is_personal_session_open_raises_on_iiko_error() -> None:
    manager, mock_api = await manager_with_stub_api("_employees_api")
    mock_api.get_personal_session_info = AsyncMock(
        return_value=GetPersonalSessionInfoResponse(correlation_id=ORG_ID, error="boom")
    )

    with pytest.raises(RuntimeError):
        await manager.is_personal_session_open(EMP_ID, ORG_ID, TG_ID)
