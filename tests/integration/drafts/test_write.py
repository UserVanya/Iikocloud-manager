"""Интеграционный danger_write lifecycle-тест Drafts (write-секция).

Цикл: create -> by_id -> save -> by_filter -> delete (cleanup в finally).
commit НЕ вызывается (создаёт реальный заказ во Front) — только unit.

menu_id / employee_id — из write-секции config.test.yml
(ключи menu_id / employee_id); без них соответствующие шаги skip.

Запуск:
    uv run pytest tests/integration/drafts -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
import os
from functools import lru_cache
from typing import Any
from uuid import UUID

import pytest
from iikocloud_client import (
    CreateDraftRequest,
    DeleteDraftRequest,
    DeliveryOrderDraft,
    FilterDraftsRequest,
    GetDraftRequest,
    SaveDraftRequest,
)
from yaml import CSafeLoader
from yaml import load as yaml_load

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


@lru_cache
def _read_config_data(path: str) -> dict[str, Any]:
    """Прочитать и распарсить config.test.yml один раз на путь за процесс."""
    with open(path, "rb") as file:
        data: dict[str, Any] = yaml_load(file, Loader=CSafeLoader)
    return data


def _write_config_key(key: str) -> str | None:
    """Необязательный ключ из write-секции config.test.yml."""
    path = os.getenv("IIKOCLOUD_TEST_CONFIG")
    if not path:
        return None
    data = _read_config_data(path)
    value = (data.get("write") or {}).get(key)
    return str(value) if value else None


@pytest.fixture
def draft_menu_id() -> str:
    """menu_id черновика из конфига (обязательное поле DeliveryOrderDraft)."""
    menu_id = _write_config_key("menu_id")
    if not menu_id:
        pytest.skip("В write-секции config.test.yml не задан menu_id")
    return menu_id


@pytest.fixture
def draft_employee_id() -> UUID:
    """employee_id для save (обязательное поле SaveDraftRequest)."""
    employee_id = _write_config_key("employee_id")
    if not employee_id:
        pytest.skip("В write-секции config.test.yml не задан employee_id")
    return UUID(employee_id)


class TestDraftLifecycle:
    async def test_create_read_save_filter_delete(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        draft_menu_id: str,
        draft_employee_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, price = product
        phone = generate_random_phone()
        draft_id: UUID | None = None
        try:
            # 1. create
            item = manager.build_product_item(product_id=product_id, price=price)
            create_response = await manager.create_delivery_draft(
                CreateDraftRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    order=DeliveryOrderDraft(
                        menu_id=draft_menu_id,
                        phone=phone,
                        items=[item],
                        order_service_type="DeliveryByClient",
                    ),
                )
            )
            assert create_response is not None
            draft_id = create_response.order_id
            assert draft_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 2. by_id
            get_response = await manager.get_delivery_draft_by_id(
                GetDraftRequest(
                    organization_id=organization_id, order_id=draft_id
                )
            )
            assert get_response is not None
            assert get_response.order is not None
            assert get_response.order.phone == phone

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. save (обновление: тот же draft id + employee_id)
            updated_draft = DeliveryOrderDraft(
                id=draft_id,
                menu_id=draft_menu_id,
                phone=phone,
                items=[item],
                comment="integration test save",
                order_service_type="DeliveryByClient",
            )
            save_response = await manager.save_delivery_draft(
                SaveDraftRequest(
                    organization_id=organization_id,
                    employee_id=draft_employee_id,
                    order=updated_draft,
                )
            )
            assert save_response.order_id == draft_id

            await asyncio.sleep(_API_PAUSE_SEC)

            # 4. by_filter — черновик находится по телефону
            filter_response = await manager.get_delivery_drafts_by_filter(
                FilterDraftsRequest(
                    organization_ids=[organization_id], phone=phone
                )
            )
            found = [
                d for d in filter_response.drafts or [] if d.id == draft_id
            ]
            assert found, "Черновик не найден через by_filter"

        finally:
            # 5. cleanup: delete
            if draft_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.delete_delivery_draft(
                        DeleteDraftRequest(
                            organization_id=organization_id,
                            order_id=draft_id,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Delete cleanup failed for draft %s: %s", draft_id, exc
                    )
