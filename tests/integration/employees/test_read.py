"""Structure-only read-тесты Employees (write-секция через test_server)."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    CourierLocationsByTimeOffsetRequest,
    CouriersRequest,
    EmployeeInfoRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestEmployeesRead:
    async def test_get_couriers_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.get_couriers(
            CouriersRequest(organization_ids=[organization_id])
        )
        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.employees is not None

    async def test_get_employee_info_by_first_courier(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        couriers = await manager.get_couriers(
            CouriersRequest(organization_ids=[organization_id])
        )
        employees = [
            e for org in couriers.employees or [] for e in org.items or []
        ]
        if not employees:
            pytest.skip("Нет сотрудников на write-стенде")
        info = await manager.get_employee_info(
            EmployeeInfoRequest(
                id=employees[0].id, organization_id=organization_id
            )
        )
        assert info is not None
        assert info.employee_info is not None
        assert info.employee_info.id == employees[0].id

    async def test_courier_location_history_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.get_courier_location_history(
            CourierLocationsByTimeOffsetRequest(
                organization_ids=[organization_id], offset_in_seconds=3600
            )
        )
        assert response is not None
        assert response.courier_locations is not None
