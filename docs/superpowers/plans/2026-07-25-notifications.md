# Notifications Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Обёртка над `send_notification` + unit- и danger_write integration-тесты (через живой заказ).

**Spec:** `docs/superpowers/specs/2026-07-25-notifications-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- Locked Names; лимит `send_notification` — 100/60s.
- SDK kwarg: `send_notification_request`. Request — полиморф; используем `OrderAttentionNotificationRequest(message_type="order_attention", organization_id, order_id, order_source, additional_info)`.
- Гейты: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура

**Files:** Modify `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`; Test `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: `ApiMethod.SEND_NOTIFICATION`; `async _ManagerBase.get_notifications_api() -> NotificationsApi`

- [ ] **Step 1: Failing test**

```python
def test_send_notification_has_limits() -> None:
    """send_notification есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    config = limits.for_method(ApiMethod("send_notification"))
    assert config.max_requests / config.time_window_seconds == pytest.approx(
        100 / 60.0
    )
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — импорт `NotificationsApi`; `SEND_NOTIFICATION = "send_notification"` в `ApiMethod`; поле в `MethodRateLimits`; слот `_notifications_api` + геттер; слот+импорт в `__init__`; поле в settings (100/60); блок в `config.example.yml`.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat: register rate limit and lazy client for notifications`

---

### Task 2: Core + helpers-заготовка + регистрация

**Files:** Create `iikocloud/mixins/notifications/{__init__,core,helpers}.py`; Modify `iikocloud/api_client_manager.py`; Test `tests/unit/test_notifications.py`

**Interfaces:**
- Produces: `send_notification(request: SendNotificationRequest) -> CorrelationIdResponse`

- [ ] **Step 1: Failing test**

`tests/unit/test_notifications.py`:

```python
"""Unit tests for Notifications domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CorrelationIdResponse,
    OrderAttentionNotificationRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_notifications_api"


async def test_send_notification_delegates() -> None:
    """send_notification проксирует CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.send_notification = AsyncMock(return_value=mock_response)

    request = OrderAttentionNotificationRequest(
        message_type="order_attention",
        organization_id=ORG_ID,
        order_id=ORG_ID,
        order_source="api",
        additional_info="i",
    )
    result = await manager.send_notification(request)

    assert result is mock_response
    mock_api.send_notification.assert_awaited_once_with(
        send_notification_request=request
    )
```

- [ ] **Step 2: Run — FAIL** (AttributeError)
- [ ] **Step 3: Реализация** — `__init__.py`; `core.py` `NotificationsCoreMixin` с одним методом (docstring: request — полиморф, сейчас поддержан подкласс order_attention); `helpers.py` заготовка; регистрация `NotificationsHelpersMixin` в MRO + docstring.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat(notifications): send_notification wrapper`

---

### Task 3: Integration danger_write (через живой заказ)

**Files:** Create `tests/integration/notifications/{__init__,test_write.py}`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`, `live_terminal_group_id`, `product`; `build_product_item`, `cancel_order`; `generate_random_phone`

- [ ] **Step 1: Тест**

`tests/integration/notifications/test_write.py`:

```python
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
```

- [ ] **Step 2: Прогон живьём** — `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/notifications -q -rs`
- [ ] **Step 3: Регрессия + гейты**
- [ ] **Step 4: Commit** `test: notification order_attention against live order`
