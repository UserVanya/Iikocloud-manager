"""Danger_write-тест Notifications (write-секция).

create заказа -> send_notification (order_attention) -> cancel (finally).

Запуск:
    uv run pytest tests/integration/notifications -v -m danger_write
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
    OrderAttentionNotificationRequest,
)

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestSendNotification:
    async def test_order_attention_for_created_order(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, price = product
        order_id: UUID | None = None
        try:
            item = manager.build_product_item(product_id=product_id, price=price)
            create_response = await manager.create_delivery_order(
                CreateOrderRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    order=DeliveryOrder(
                        phone=generate_random_phone(),
                        items=[item],
                        order_service_type="DeliveryByClient",
                    ),
                )
            )
            order_info = create_response.order_info
            assert order_info is not None
            status_value = getattr(order_info.creation_status, "value", None)
            assert status_value != "Error", (
                f"Create failed: {order_info.error_info}"
            )
            order_id = order_info.id
            assert order_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            response = await manager.send_notification(
                OrderAttentionNotificationRequest(
                    message_type="order_attention",
                    organization_id=organization_id,
                    order_id=order_id,
                    order_source="iikocloud-manager-test",
                    additional_info="integration test notification",
                )
            )
            assert response is not None
            assert response.correlation_id is not None

        finally:
            if order_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_order(
                        organization_id=organization_id,
                        order_id=order_id,
                        cancel_comment="integration test cleanup",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Cancel cleanup failed: %s", exc)
