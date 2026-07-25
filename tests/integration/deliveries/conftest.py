"""Фикстуры для интеграционных тестов deliveries (write-стенд)."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
import pytest_asyncio
from iikocloud_client import (
    NomenclatureRequest,
    TerminalGroupsIsAliveRequest,
    TerminalGroupsRequest,
)

from iikocloud import IikoCloudApiClientManager


@pytest_asyncio.fixture(loop_scope="session")
async def live_terminal_group_id(
    manager: IikoCloudApiClientManager, organization_id: UUID
) -> UUID:
    """Первая терминальная группа; skip, если фронт офлайн."""
    response = await manager.get_terminal_groups(
        TerminalGroupsRequest(organization_ids=[organization_id])
    )
    groups = [g for org in response.terminal_groups for g in org.items]
    if not groups:
        pytest.skip("Нет терминальных групп на write-стенде")
    group_id = groups[0].id

    alive = await manager.check_terminal_groups_availability(
        TerminalGroupsIsAliveRequest(
            organization_ids=[organization_id],
            terminal_group_ids=[group_id],
        )
    )
    if not any(s.is_alive for s in alive.is_alive_status):
        pytest.skip(
            "Терминальная группа write-стенда офлайн (is_alive=False) — "
            "заказ некому исполнять"
        )
    return group_id


@pytest_asyncio.fixture(loop_scope="session")
async def product(
    manager: IikoCloudApiClientManager, organization_id: UUID
):
    """Первый неудалённый продукт номенклатуры с ценой из sizePrices."""
    response = await manager.get_nomenclature(
        NomenclatureRequest(organization_id=organization_id, start_revision=0)
    )
    for p in response.products:
        if getattr(p, "is_deleted", False):
            continue
        prices = [
            sp.price.current_price
            for sp in (p.size_prices or [])
            if sp.price and sp.price.current_price
        ]
        if prices:
            return p.id, prices[0]
    pytest.skip("Нет продуктов с ценой в номенклатуре write-стенда")
