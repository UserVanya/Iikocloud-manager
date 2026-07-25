"""Интеграционный danger_write-тест Deliveries create & update (write-секция).

Полный цикл по живому заказу: create -> change_comment /
change_complete_before -> cancel (cleanup в finally).
Заказ остаётся на стенде со статусом Cancelled — физического
удаления в API нет.

Требуется живая терминальная группа (is_alive) — иначе skip.

Запуск:
    uv run pytest tests/integration/deliveries -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID

import pytest
from iikocloud_client import (
    ChangeCompleteBeforeRequest,
    ChangeDeliveryCommentRequest,
    CreateOrderRequest,
    DeliveryOrder,
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


class TestDeliveryLifecycle:
    async def test_create_change_cancel_delivery(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, price = product
        order_id: UUID | None = None
        try:
            # 1. create
            item = manager.build_product_item(product_id=product_id, price=price)
            create_response = await manager.create_delivery_order(
                CreateOrderRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    order=DeliveryOrder(
                        phone=generate_random_phone(),
                        order_service_type="DeliveryByClient",
                        items=[item],
                    ),
                )
            )
            assert create_response is not None
            assert create_response.correlation_id is not None
            order_info = create_response.order_info
            assert order_info is not None
            assert order_info.creation_status is not None
            status_value = getattr(order_info.creation_status, "value", None)
            assert status_value != "Error", (
                f"Create failed: {order_info.error_info}"
            )
            order_id = order_info.id
            assert order_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 2. change_comment
            comment_response = await manager.change_delivery_comment(
                ChangeDeliveryCommentRequest(
                    organization_id=organization_id,
                    order_id=order_id,
                    comment="integration test comment",
                )
            )
            assert comment_response.correlation_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. change_complete_before
            new_time = (datetime.now() + timedelta(hours=3)).strftime(
                "%Y-%m-%d %H:%M:%S.000"
            )
            time_response = await manager.change_delivery_complete_before(
                ChangeCompleteBeforeRequest(
                    organization_id=organization_id,
                    order_id=order_id,
                    new_complete_before=new_time,
                )
            )
            assert time_response.correlation_id is not None

        finally:
            # 4. cleanup: cancel (заказ остаётся в истории со статусом Cancelled)
            if order_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_order(
                        organization_id=organization_id,
                        order_id=order_id,
                        cancel_comment="integration test cleanup",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Cancel cleanup failed for order %s: %s", order_id, exc
                    )
