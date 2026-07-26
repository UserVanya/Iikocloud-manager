"""Danger_write-тест Operations (write-секция).

stop_list add (команда) -> get_command_status -> wait_command -> cleanup.

Запуск:
    uv run pytest tests/integration/operations -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    AddProductsToStopListItem,
    AddProductsToStopListRequest,
    ClearStopListRequest,
    ErrorCommandStatus,
    GetCommandStatusRequest,
    SuccessCommandStatus,
)

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestCommandStatus:
    async def test_status_and_wait_for_stop_list_command(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, _ = product
        try:
            add_response = await manager.add_products_to_stop_list(
                AddProductsToStopListRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    items=[
                        AddProductsToStopListItem(
                            product_id=product_id, balance=0.0
                        )
                    ],
                )
            )
            correlation_id = add_response.correlation_id
            assert correlation_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # get_command_status — валидный ответ (InProgress или Success)
            status = await manager.get_command_status(
                GetCommandStatusRequest(
                    organization_id=organization_id,
                    correlation_id=correlation_id,
                )
            )
            assert status is not None
            assert getattr(status, "state", None) in (
                "Success",
                "InProgress",
                "Error",
            )

            # wait_command — терминальный статус
            final = await manager.wait_command(
                correlation_id, organization_id, timeout=60.0
            )
            assert isinstance(
                final, (SuccessCommandStatus, ErrorCommandStatus)
            )
            if isinstance(final, ErrorCommandStatus):
                pytest.fail(f"Команда стоп-листа завершилась ошибкой: {final.error_reason}")

        finally:
            try:
                await asyncio.sleep(_API_PAUSE_SEC)
                await manager.clear_stop_list(
                    ClearStopListRequest(
                        organization_id=organization_id,
                        terminal_group_id=live_terminal_group_id,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("clear_stop_list cleanup: %s", exc)
