"""Интеграционные danger_write-тесты стоп-листов (write-секция).

Цикл: add -> check (продукт в rejectedItems) -> remove -> check (чисто) -> clear.
Требуются: iiko >= 8.6.1, права 'Data: changing stoplists', терминальная
группа и реальный продукт организации.

Запуск:
    uv run pytest tests/integration/menu/test_stop_lists_write.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
import pytest_asyncio
from iikocloud_client import (
    AddProductsToStopListItem,
    AddProductsToStopListRequest,
    CheckStopListRequest,
    ClearStopListRequest,
    DeliveryOrderCreateProductItem,
    NomenclatureRequest,
    RemoveProductsFromStopListItem,
    RemoveProductsFromStopListRequest,
    TerminalGroupsRequest,
)
from iikocloud_client.exceptions import ApiException

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0
_POLL_ATTEMPTS = 10
_POLL_INTERVAL_SEC = 3.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


def _is_stop_list_unavailable(exc: BaseException) -> bool:
    body = getattr(exc, "body", None) or str(exc)
    return "stoplist" in body.lower() or "stop_list" in body.lower() or "Forbidden" in body


@pytest_asyncio.fixture(loop_scope="session")
async def terminal_group_id(
    manager: IikoCloudApiClientManager, organization_id: UUID
) -> UUID:
    """Первая терминальная группа организации (не в sleep)."""
    response = await manager.get_terminal_groups(
        TerminalGroupsRequest(organization_ids=[organization_id])
    )
    groups = [g for org in response.terminal_groups for g in org.items]
    if not groups:
        pytest.skip("Нет терминальных групп на write-стенде")
    return groups[0].id


@pytest_asyncio.fixture(loop_scope="session")
async def product_id(
    manager: IikoCloudApiClientManager, organization_id: UUID
) -> UUID:
    """Реальный продукт из номенклатуры write-организации."""
    response = await manager.get_nomenclature(
        NomenclatureRequest(organization_id=organization_id, start_revision=0)
    )
    products = [p for p in response.products if not getattr(p, "is_deleted", False)]
    if not products:
        pytest.skip("Нет продуктов в номенклатуре write-стенда")
    return products[0].id


class TestStopListLifecycle:
    async def test_add_check_remove_clear_cycle(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        terminal_group_id: UUID,
        product_id: UUID,
    ) -> None:
        try:
            # 1. add
            await manager.add_products_to_stop_list(
                AddProductsToStopListRequest(
                    organization_id=organization_id,
                    terminal_group_id=terminal_group_id,
                    items=[
                        AddProductsToStopListItem(product_id=product_id, balance=0.0)
                    ],
                )
            )

            # 2. check — продукт появился (поллинг: мутация асинхронная)
            async def _rejected() -> list:
                resp = await manager.check_products_in_stop_list(
                    CheckStopListRequest(
                        organization_id=organization_id,
                        terminal_group_id=terminal_group_id,
                        items=[
                            DeliveryOrderCreateProductItem(
                                type="Product",
                                product_id=product_id,
                                amount=1.0,
                                price=1.0,
                            )
                        ],
                    )
                )
                return list(resp.rejected_items or [])

            rejected = []
            for _ in range(_POLL_ATTEMPTS):
                await asyncio.sleep(_POLL_INTERVAL_SEC)
                rejected = await _rejected()
                if any(item.product_id == product_id for item in rejected):
                    break
            assert any(item.product_id == product_id for item in rejected), (
                "Продукт не появился в стоп-листе после add"
            )

            # 3. remove + финальный clear (cleanup в любом случае)
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.remove_products_from_stop_list(
                RemoveProductsFromStopListRequest(
                    organization_id=organization_id,
                    terminal_group_id=terminal_group_id,
                    items=[RemoveProductsFromStopListItem(product_id=product_id)],
                )
            )

            # 4. check — продукт исчез (поллинг: мутация асинхронная)
            for _ in range(_POLL_ATTEMPTS):
                await asyncio.sleep(_POLL_INTERVAL_SEC)
                rejected = await _rejected()
                if not any(item.product_id == product_id for item in rejected):
                    break
            assert not any(item.product_id == product_id for item in rejected), (
                "Продукт не исчез из стоп-листа после remove"
            )
        except ApiException as exc:
            if _is_stop_list_unavailable(exc):
                pytest.skip(f"Стенд не поддерживает мутации стоп-листов: {exc}")
            raise
        finally:
            try:
                await asyncio.sleep(_API_PAUSE_SEC)
                await manager.clear_stop_list(
                    ClearStopListRequest(
                        organization_id=organization_id,
                        terminal_group_id=terminal_group_id,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("clear_stop_list cleanup: %s", exc)
