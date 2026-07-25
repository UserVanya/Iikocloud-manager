"""Structure-only read-тесты DeliveriesRetrieve (write-секция через test_server).

Проверяем вызов + структуру ответа без привязки к данным стенда.

Запуск:
    uv run pytest tests/integration/deliveries/test_read_structure.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from iikocloud_client import (
    DeliveryStatus,
    OrdersByDeliveryDateAndPhoneRequest,
    OrdersByDeliveryDateAndStatusRequest,
    OrdersByRevisionRequest,
    OrdersHistoryByDeliveryDateAndPhoneRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.000"


class TestRetrieveStructure:
    async def test_by_delivery_date_and_phone(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_deliveries_by_delivery_date_and_phone(
            OrdersByDeliveryDateAndPhoneRequest(
                organization_ids=[organization_id],
                phone="+70000000000",
                delivery_date_from=(datetime.now() - timedelta(days=1)).strftime(
                    _DATE_FORMAT
                ),
            )
        )
        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.orders_by_organizations is not None

    async def test_by_delivery_date_and_status(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_deliveries_by_delivery_date_and_status(
            OrdersByDeliveryDateAndStatusRequest(
                organization_ids=[organization_id],
                delivery_date_from=(datetime.now() - timedelta(days=1)).strftime(
                    _DATE_FORMAT
                ),
                statuses=[DeliveryStatus.CANCELLED],
            )
        )
        assert response is not None
        assert response.orders_by_organizations is not None

    async def test_by_revision(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """start_revision=0: стенд может отклонить окно > 3ч — тогда skip."""
        from iikocloud_client.exceptions import ApiException

        try:
            response = await manager.get_deliveries_by_revision(
                OrdersByRevisionRequest(
                    organization_ids=[organization_id], start_revision=0
                )
            )
        except ApiException as exc:
            pytest.skip(f"Стенд отклонил start_revision=0 (окно 3ч): {exc}")
        assert response is not None
        assert response.orders_by_organizations is not None
        assert isinstance(response.max_revision, int)

    async def test_history_by_phone(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_delivery_history_by_delivery_date_and_phone(
            OrdersHistoryByDeliveryDateAndPhoneRequest(
                organization_ids=[organization_id],
                phone="+70000000000",
                rows_count=10,
            )
        )
        assert response is not None
        assert response.orders_by_organizations is not None
