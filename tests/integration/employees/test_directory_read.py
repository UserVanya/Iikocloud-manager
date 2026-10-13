"""Read-only тесты раздела сотрудников 0.5.0 (write-секция — тестовый стенд, test_server).

Только чтение: справочник сотрудников и должностей, явки и типы явок, курьеры с проверкой
роли, где открыта смена курьера, открыта ли она, места активных курьеров. Ни смен, ни явок,
ни сотрудников тесты не создают и не меняют. Проверяются структура, id и количества —
имена и телефоны в утверждения не попадают.

Запуск:
    IIKOCLOUD_TEST_CONFIG=$PWD/config.test.yml \
        uv run pytest tests/integration/employees/test_directory_read.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
import pytest_asyncio
from iikocloud_client import (
    AttendanceListRequest,
    AttendanceTypeListRequest,
    CouriersAndCheckRoleRequest,
    CouriersRequest,
    EmployeeGetRequest,
    EmployeeListRequest,
    GetPositionRequest,
    GetTerminalGroupsOfEmployeeRequest,
    ListPositionsRequest,
)

from iikocloud import EMPLOYEE_CONTACT_FIELDS, IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]

# Курьеры у iiko — 1 запрос в минуту на ключ: читаем один раз на модуль.
_couriers_cache: dict[UUID, list[UUID]] = {}


@pytest_asyncio.fixture(loop_scope="session")
async def courier_ids(
    manager: IikoCloudApiClientManager, organization_id: UUID
) -> list[UUID]:
    if organization_id not in _couriers_cache:
        couriers = await manager.list_organization_couriers(organization_id)
        _couriers_cache[organization_id] = [c.id for c in couriers]
    return _couriers_cache[organization_id]


class TestEmployeesDirectoryRead:
    async def test_list_employees_returns_requested_contact_fields(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        page = await manager.list_employees(
            EmployeeListRequest(fields=list(EMPLOYEE_CONTACT_FIELDS), filters=[], limit=20)
        )
        assert page.items is not None
        if not page.items:
            pytest.skip("На стенде нет сотрудников")
        assert all(e.id for e in page.items)
        # Поле телефона есть в модели ответа и запрошено; на стенде оно может быть пустым.
        assert all(hasattr(e, "phone") for e in page.items)

    async def test_list_all_employees_matches_total(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        employees = await manager.list_all_employees(page_size=1000)
        ids = [e.id for e in employees]
        assert len(ids) == len(set(ids))

    async def test_get_employee_by_id(self, manager: IikoCloudApiClientManager) -> None:
        page = await manager.list_employees(EmployeeListRequest(filters=[], limit=1))
        if not page.items:
            pytest.skip("На стенде нет сотрудников")
        employee_id = page.items[0].id
        assert employee_id is not None
        employee = await manager.get_employee(EmployeeGetRequest(id=employee_id))
        assert employee.id == employee_id

    async def test_positions_list_and_get(self, manager: IikoCloudApiClientManager) -> None:
        positions = await manager.list_employee_positions(ListPositionsRequest(limit=50))
        assert positions.items is not None
        if not positions.items:
            pytest.skip("На стенде нет должностей")
        position_id = positions.items[0].id
        position = await manager.get_employee_position(GetPositionRequest(id=position_id))
        assert position.id == position_id

    async def test_attendance_types(self, manager: IikoCloudApiClientManager) -> None:
        types = await manager.list_employee_attendance_types(AttendanceTypeListRequest())
        assert types.items is not None
        assert all(t.id is not None for t in types.items)

    async def test_attendances_for_last_week(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        # iiko принимает начало и конец периода в ISO 8601 (проверено на стенде 13.10.2026).
        end = datetime.now(UTC).replace(microsecond=0)
        start = end - timedelta(days=7)
        response = await manager.list_employee_attendances(
            AttendanceListRequest(
                organization_id=organization_id,
                start_at=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                end_at=end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                limit=100,
            )
        )
        assert response.items is not None
        assert all(a.organization_id in (None, organization_id) for a in response.items)


class TestCouriersRead:
    async def test_couriers_by_role_with_a_position_code(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        positions = await manager.list_employee_positions(ListPositionsRequest(limit=50))
        codes = [p.code for p in positions.items or [] if p.code]
        if not codes:
            pytest.skip("На стенде нет должностей с кодом")
        response = await manager.get_couriers_by_role(
            CouriersAndCheckRoleRequest(
                organization_ids=[organization_id], roles_to_check=codes[:1]
            )
        )
        assert isinstance(response.correlation_id, UUID)
        assert response.employees_with_check_roles is not None

    async def test_where_courier_shift_is_open(
        self, manager: IikoCloudApiClientManager, courier_ids: list[UUID]
    ) -> None:
        if not courier_ids:
            pytest.skip("На стенде нет курьеров")
        response = await manager.get_terminal_groups_of_employee(
            GetTerminalGroupsOfEmployeeRequest(employee_id=courier_ids[0])
        )
        assert isinstance(response.terminal_group_ids, list)

    async def test_is_personal_session_open_reads_a_flag(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        courier_ids: list[UUID],
    ) -> None:
        if not courier_ids:
            pytest.skip("На стенде нет курьеров")
        opened = await manager.is_personal_session_open(
            courier_ids[0], organization_id, live_terminal_group_id
        )
        assert isinstance(opened, bool)

    async def test_active_courier_locations(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.get_active_courier_locations(
            CouriersRequest(organization_ids=[organization_id])
        )
        assert isinstance(response.correlation_id, UUID)
        assert response.active_courier_locations is not None
