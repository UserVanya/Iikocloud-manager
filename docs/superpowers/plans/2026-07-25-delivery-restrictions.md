# DeliveryRestrictions Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обёртки над 2 методами `DeliveryRestrictionsApi` + unit- и structure-only integration-тесты.

**Architecture:** Новый домен `iikocloud/mixins/delivery_restrictions/` (`core.py` + `helpers.py`-заготовка), регистрация через `DeliveryRestrictionsHelpersMixin` в MRO.

**Spec:** `docs/superpowers/specs/2026-07-25-delivery-restrictions-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- `ApiMethod` value == snake_case имени метода SDK == имя поля в `MethodRateLimitsSettings` и `MethodRateLimits` (Locked Names).
- Rate limits: `get_allowed_delivery_restrictions` — 20/60s; `get_delivery_restrictions` — 1/60s.
- SDK kwargs: `get_allowed_restrictions_request`, `get_delivery_restrictions_request`.
- Проверки качества после каждой задачи: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура (ApiMethod, лимиты, lazy-клиент)

**Files:**
- Modify: `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: `ApiMethod.GET_ALLOWED_DELIVERY_RESTRICTIONS`, `ApiMethod.GET_DELIVERY_RESTRICTIONS`; `async _ManagerBase.get_delivery_restrictions_api() -> DeliveryRestrictionsApi`

- [ ] **Step 1: Failing test**

В `tests/unit/test_config_reader.py`:

```python
def test_delivery_restrictions_methods_have_limits() -> None:
    """2 метода delivery_restrictions есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "get_allowed_delivery_restrictions": 20 / 60.0,
        "get_delivery_restrictions": 1 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)
```

- [ ] **Step 2: Run — FAIL** (`ValueError: ... is not a valid ApiMethod`)

- [ ] **Step 3: Реализация**

В `iikocloud/mixins/_base.py`:
1. Импорт `DeliveryRestrictionsApi` (алфавитно).
2. В `ApiMethod` (секция после deliveries retrieve):

```python
    # Delivery Restrictions
    GET_ALLOWED_DELIVERY_RESTRICTIONS = "get_allowed_delivery_restrictions"
    GET_DELIVERY_RESTRICTIONS = "get_delivery_restrictions"
```

3. В `MethodRateLimits` — 2 поля `RateLimitConfig` с теми же именами.
4. Слот `_delivery_restrictions_api: DeliveryRestrictionsApi | None` + геттер:

```python
    async def get_delivery_restrictions_api(self) -> DeliveryRestrictionsApi:
        """Получить клиент DeliveryRestrictionsApi."""
        await self._ensure_token_manager()
        if self._delivery_restrictions_api is None:
            self._delivery_restrictions_api = DeliveryRestrictionsApi(
                api_client=self._api_client
            )
        return self._delivery_restrictions_api
```

В `iikocloud/api_client_manager.py.__init__`: `self._delivery_restrictions_api = None` + импорт.

В `iikocloud/config_reader.py` (комментарий `# Delivery Restrictions`):

```python
    get_allowed_delivery_restrictions: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    get_delivery_restrictions: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
```

В `config.example.yml` — 2 блока с теми же значениями.

- [ ] **Step 4: Run — PASS + качество**: unit 139 passed, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/api_client_manager.py iikocloud/config_reader.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limits and lazy client for delivery restrictions"
```

---

### Task 2: Core + helpers-заготовка + регистрация

**Files:**
- Create: `iikocloud/mixins/delivery_restrictions/{__init__,core,helpers}.py`
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO + docstring)
- Test: `tests/unit/test_delivery_restrictions.py`

**Interfaces:**
- Produces:
  - `DeliveryRestrictionsCoreMixin.get_allowed_delivery_restrictions(request: GetAllowedRestrictionsRequest) -> GetAllowedRestrictionsResponse`
  - `DeliveryRestrictionsCoreMixin.get_delivery_restrictions(request: GetDeliveryRestrictionsRequest) -> GetDeliveryRestrictionsResponse`
  - `DeliveryRestrictionsHelpersMixin(DeliveryRestrictionsCoreMixin)` — заготовка без методов

- [ ] **Step 1: Failing tests**

`tests/unit/test_delivery_restrictions.py`:

```python
"""Unit tests for DeliveryRestrictions domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    GetAllowedRestrictionsRequest,
    GetAllowedRestrictionsResponse,
    GetDeliveryRestrictionsRequest,
    GetDeliveryRestrictionsResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_delivery_restrictions_api"


async def test_get_allowed_delivery_restrictions_delegates() -> None:
    """get_allowed_delivery_restrictions проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetAllowedRestrictionsResponse)
    mock_api.get_allowed_delivery_restrictions = AsyncMock(
        return_value=mock_response
    )

    request = GetAllowedRestrictionsRequest(
        is_courier_delivery=True, organization_ids=[ORG_ID]
    )
    result = await manager.get_allowed_delivery_restrictions(request)

    assert result is mock_response
    mock_api.get_allowed_delivery_restrictions.assert_awaited_once_with(
        get_allowed_restrictions_request=request
    )


async def test_get_delivery_restrictions_delegates() -> None:
    """get_delivery_restrictions проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetDeliveryRestrictionsResponse)
    mock_api.get_delivery_restrictions = AsyncMock(return_value=mock_response)

    request = GetDeliveryRestrictionsRequest(organization_ids=[ORG_ID])
    result = await manager.get_delivery_restrictions(request)

    assert result is mock_response
    mock_api.get_delivery_restrictions.assert_awaited_once_with(
        get_delivery_restrictions_request=request
    )
```

- [ ] **Step 2: Run — FAIL** (AttributeError)

- [ ] **Step 3: Реализация**

`iikocloud/mixins/delivery_restrictions/__init__.py`:

```python
"""DeliveryRestrictions domain mixins."""

from iikocloud.mixins.delivery_restrictions.core import (
    DeliveryRestrictionsCoreMixin,
)
from iikocloud.mixins.delivery_restrictions.helpers import (
    DeliveryRestrictionsHelpersMixin,
)

__all__ = ["DeliveryRestrictionsCoreMixin", "DeliveryRestrictionsHelpersMixin"]
```

`iikocloud/mixins/delivery_restrictions/core.py`:

```python
"""DeliveryRestrictions core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    GetAllowedRestrictionsRequest,
    GetAllowedRestrictionsResponse,
    GetDeliveryRestrictionsRequest,
    GetDeliveryRestrictionsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DeliveryRestrictionsCoreMixin(_ManagerBase):
    """Core-методы DeliveryRestrictions API (оба read-only)."""

    async def get_allowed_delivery_restrictions(
        self,
        request: GetAllowedRestrictionsRequest,
    ) -> GetAllowedRestrictionsResponse:
        """Подходящие терминальные группы под адрес/сумму/дату доставки.

        Ответ: is_allowed + allowed_items (терминалы с длительностью)
        и rejected_items с кодами причин отказа.
        """

        async def api_call() -> GetAllowedRestrictionsResponse:
            api = await self.get_delivery_restrictions_api()
            return await api.get_allowed_delivery_restrictions(
                get_allowed_restrictions_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_ALLOWED_DELIVERY_RESTRICTIONS, api_call
        )

    async def get_delivery_restrictions(
        self,
        request: GetDeliveryRestrictionsRequest,
    ) -> GetDeliveryRestrictionsResponse:
        """Справочник ограничений доставки (зоны, мин. суммы, интервалы)."""

        async def api_call() -> GetDeliveryRestrictionsResponse:
            api = await self.get_delivery_restrictions_api()
            return await api.get_delivery_restrictions(
                get_delivery_restrictions_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERY_RESTRICTIONS, api_call
        )
```

`iikocloud/mixins/delivery_restrictions/helpers.py`:

```python
"""DeliveryRestrictions helpers mixin — convenience-методы (заготовка)."""

from iikocloud.mixins.delivery_restrictions.core import (
    DeliveryRestrictionsCoreMixin,
)


class DeliveryRestrictionsHelpersMixin(DeliveryRestrictionsCoreMixin):
    """Публичный delivery-restrictions mixin (helpers появятся позже)."""
```

В `iikocloud/api_client_manager.py`: импорт `DeliveryRestrictionsHelpersMixin`, в MRO после `DeliveriesRetrieveHelpersMixin,`, docstring: `deliveries, deliveries_retrieve, delivery_restrictions.`

- [ ] **Step 4: Run — PASS + качество**: unit 141 passed, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/delivery_restrictions iikocloud/api_client_manager.py tests/unit/test_delivery_restrictions.py
git commit -m "feat(delivery-restrictions): allowed/retrieve restrictions wrappers"
```

---

### Task 3: Integration structure-only

**Files:**
- Create: `tests/integration/delivery_restrictions/__init__.py` (пустой)
- Create: `tests/integration/delivery_restrictions/test_read.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`; маркер `test_server` (write-секция — на read-организации ограничений может не быть)

- [ ] **Step 1: Тест**

`tests/integration/delivery_restrictions/test_read.py`:

```python
"""Structure-only read-тесты DeliveryRestrictions (write-секция через test_server).

Запуск:
    uv run pytest tests/integration/delivery_restrictions -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    GetAllowedRestrictionsRequest,
    GetDeliveryRestrictionsRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestDeliveryRestrictionsRead:
    async def test_get_delivery_restrictions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_delivery_restrictions(
            GetDeliveryRestrictionsRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.delivery_restrictions is not None

    async def test_get_allowed_delivery_restrictions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Без адреса/суммы сервер может ответить rejected — это валидно,
        проверяем структуру, а не бизнес-результат."""
        response = await manager.get_allowed_delivery_restrictions(
            GetAllowedRestrictionsRequest(
                is_courier_delivery=True,
                organization_ids=[organization_id],
            )
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.is_allowed is not None
        assert response.allowed_items is not None
        assert response.rejected_items is not None
```

- [ ] **Step 2: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/delivery_restrictions -q -rs`
Expected: PASS (или skip с явной причиной — тогда зафиксировать).

- [ ] **Step 3: Регрессия + качество**: unit 141 passed, ruff/mypy чисто
- [ ] **Step 4: Commit**

```bash
git add tests/integration/delivery_restrictions
git commit -m "test: delivery restrictions structure-only integration tests"
```
