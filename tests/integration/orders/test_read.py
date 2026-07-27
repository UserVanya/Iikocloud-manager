"""Structure-only read-тесты Orders (write-секция через test_server)."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    GetTableOrdersByIdRequest,
    GetTableOrdersByTableRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestOrdersRead:
    async def test_by_id_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """По несуществующему id — валидная структура (список может быть пуст)."""
        response = await manager.get_table_orders_by_id(
            GetTableOrdersByIdRequest(
                organization_ids=[organization_id],
                order_ids=[UUID("00000000-0000-0000-0000-000000000001")],
            )
        )
        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.orders is not None

    async def test_by_table_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
    ) -> None:
        from iikocloud_client import GetRestaurantSectionsRequest

        sections = await manager.get_reserve_restaurant_sections(
            GetRestaurantSectionsRequest(
                terminal_group_ids=[live_terminal_group_id]
            )
        )
        tables = [
            t
            for s in sections.restaurant_sections or []
            for t in s.tables or []
        ]
        if not tables:
            pytest.skip("Нет столиков на write-стенде")
        response = await manager.get_table_orders_by_table(
            GetTableOrdersByTableRequest(
                organization_ids=[organization_id],
                table_ids=[tables[0].id],
            )
        )
        assert response is not None
        assert response.orders is not None
