"""Danger_write lifecycle-тест Orders (write-секция).

sections -> столик -> create -> by_id -> add_items -> by_table
-> cancel (fallback close при iiko < 9.0.5) в finally.

Запуск:
    uv run pytest tests/integration/orders/test_lifecycle.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    AddItemsToTableOrderRequest,
    CancelTableOrderRequest,
    CloseTableOrderRequest,
    CreateTableOrderRequest,
    GetRestaurantSectionsRequest,
    GetTableOrdersByIdRequest,
    GetTableOrdersByTableRequest,
    TableOrderRequest,
)
from iikocloud_client.exceptions import ApiException

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


def _is_cancel_unsupported(exc: BaseException) -> bool:
    """Стенд < 9.0.5 или cancel недоступен для заказа."""
    body = getattr(exc, "body", None) or str(exc)
    lowered = body.lower()
    return "9.0.5" in body or "not supported" in lowered or (
        "cancel" in lowered and "status" in lowered
    )


class TestTableOrderLifecycle:
    async def test_create_read_add_items_cancel(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, price = product
        # Столик из секций
        sections = await manager.get_reserve_restaurant_sections(
            GetRestaurantSectionsRequest(
                terminal_group_ids=[live_terminal_group_id]
            )
        )
        tables = [
            t
            for s in sections.restaurant_sections or []
            for t in s.tables or []
            if not getattr(t, "is_deleted", False)
        ]
        if not tables:
            pytest.skip("Нет столиков на write-стенде")
        table_id = tables[0].id

        order_id: UUID | None = None
        try:
            # 1. create
            item = manager.build_product_item(product_id=product_id, price=price)
            create_response = await manager.create_table_order(
                CreateTableOrderRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    order=TableOrderRequest(items=[item], table_ids=[table_id]),
                )
            )
            assert create_response is not None
            order_info = create_response.order_info
            assert order_info is not None
            status_value = getattr(order_info.creation_status, "value", None)
            assert status_value != "Error", (
                f"Create failed: {order_info.error_info}"
            )
            order_id = order_info.id
            assert order_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 2. by_id — заказ читается
            by_id = await manager.get_table_orders_by_id(
                GetTableOrdersByIdRequest(
                    organization_ids=[organization_id], order_ids=[order_id]
                )
            )
            found = [o for o in by_id.orders or [] if o.id == order_id]
            assert found, "Заказ не найден через by_id"

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. add_items
            add_response = await manager.add_items_to_table_order(
                AddItemsToTableOrderRequest(
                    organization_id=organization_id,
                    order_id=order_id,
                    items=[manager.build_product_item(product_id=product_id, price=price)],
                )
            )
            assert add_response.correlation_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 4. by_table — заказ висит на столике
            by_table = await manager.get_table_orders_by_table(
                GetTableOrdersByTableRequest(
                    organization_ids=[organization_id], table_ids=[table_id]
                )
            )
            on_table = [o for o in by_table.orders or [] if o.id == order_id]
            assert on_table, "Заказ не найден через by_table"

        finally:
            # 5. cleanup: cancel (fallback close при старой версии стенда)
            if order_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_table_order(
                        CancelTableOrderRequest(
                            organization_id=organization_id, order_id=order_id
                        )
                    )
                except ApiException as exc:
                    if not _is_cancel_unsupported(exc):
                        logger.error(
                            "Cancel failed для заказа %s: %s", order_id, exc
                        )
                    else:
                        try:
                            await manager.close_table_order(
                                CloseTableOrderRequest(
                                    organization_id=organization_id,
                                    order_id=order_id,
                                )
                            )
                        except Exception as close_exc:  # noqa: BLE001
                            logger.error(
                                "CLEANUP FAILED: заказ %s остался на столике "
                                "стенда (cancel: %s; close: %s)",
                                order_id,
                                exc,
                                close_exc,
                            )
