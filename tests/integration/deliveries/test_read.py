"""Read-back danger_write-тест DeliveriesRetrieve (write-секция).

create -> get_delivery_by_id -> search_deliveries по телефону -> cancel.
Проверяет, что созданный заказ реально читается retrieve-методами.

Запуск:
    uv run pytest tests/integration/deliveries/test_read.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    CreateOrderRequest,
    DeliveryOrder,
    OrdersByDeliveryDateAndFilterRequest,
)

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0
_READBACK_ATTEMPTS = 5
_READBACK_INTERVAL_SEC = 2.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestDeliveryReadback:
    async def test_created_order_is_readable(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, price = product
        phone = generate_random_phone()
        order_id: UUID | None = None
        try:
            # 1. create
            item = manager.build_product_item(product_id=product_id, price=price)
            create_response = await manager.create_delivery_order(
                CreateOrderRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    order=DeliveryOrder(
                        phone=phone,
                        items=[item],
                        order_service_type="DeliveryByClient",
                    ),
                )
            )
            order_info = create_response.order_info
            assert order_info is not None
            status_value = getattr(order_info.creation_status, "value", None)
            assert status_value != "Error", f"Create failed: {order_info.error_info}"
            order_id = order_info.id
            assert order_id is not None

            # 2. get_delivery_by_id (bounded-поллинг: индексация не мгновенная)
            found = None
            for _ in range(_READBACK_ATTEMPTS):
                await asyncio.sleep(_READBACK_INTERVAL_SEC)
                found = await manager.get_delivery_by_id(organization_id, order_id)
                if found is not None:
                    break
            assert found is not None, "Заказ не появился в get_deliveries_by_id"
            assert found.id == order_id
            # phone живёт уровнем ниже: OrderInfo.order (nullable payload)
            assert found.order is not None
            assert found.order.phone == phone

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. search_deliveries по телефону
            found_by_phone = []
            for _ in range(_READBACK_ATTEMPTS):
                await asyncio.sleep(_READBACK_INTERVAL_SEC)
                search_response = await manager.search_deliveries(
                    OrdersByDeliveryDateAndFilterRequest(
                        organization_ids=[organization_id],
                        search_text=phone,
                    )
                )
                found_by_phone = [
                    order
                    for org_orders in search_response.orders_by_organizations or []
                    for order in org_orders.orders or []
                    if order.id == order_id
                ]
                if found_by_phone:
                    break
            assert found_by_phone, "Заказ не найден через search_deliveries"

        finally:
            # 4. cleanup: cancel
            if order_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_order(
                        organization_id=organization_id,
                        order_id=order_id,
                        cancel_comment="integration read-back cleanup",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Cancel cleanup failed for order %s: %s", order_id, exc
                    )
