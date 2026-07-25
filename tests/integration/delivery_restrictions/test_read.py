"""Structure-only read-тесты DeliveryRestrictions (write-секция через test_server).

Запуск:
    uv run pytest tests/integration/delivery_restrictions -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    GetAllowedRestrictionsRequest,
    GetDeliveryRestrictionsRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestDeliveryRestrictionsRead:
    async def test_get_delivery_restrictions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_delivery_restrictions(
            GetDeliveryRestrictionsRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.delivery_restrictions is not None

    async def test_get_allowed_delivery_restrictions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Без адреса/суммы сервер может ответить rejected — это валидно,
        проверяем структуру, а не бизнес-результат."""
        response = await manager.get_allowed_delivery_restrictions(
            GetAllowedRestrictionsRequest(
                is_courier_delivery=True,
                organization_ids=[organization_id],
            )
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.is_allowed is not None
        assert response.allowed_items is not None
        assert response.rejected_items is not None
