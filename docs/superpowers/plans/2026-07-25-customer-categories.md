# CustomerCategories Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обёртки над 3 методами `CustomerCategoriesApi` + unit- и integration-тесты (structure + danger_write цикл).

**Architecture:** Новый домен `iikocloud/mixins/customer_categories/` (`core.py` + `helpers.py`-заготовка), регистрация через `CustomerCategoriesHelpersMixin` в MRO.

**Spec:** `docs/superpowers/specs/2026-07-25-customer-categories-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель; add/remove возвращают `None` (object-ответ).
- `ApiMethod` value == snake_case имени метода SDK (Locked Names).
- Rate limits: `get_customer_categories` — 1/60s; `add_customer_category`, `remove_customer_category` — 100/60s.
- SDK kwargs: `get_categories_request`, `change_category_for_customer_request` (у ОБЕИХ мутаций).
- Проверки качества: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура

**Files:**
- Modify: `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: `ApiMethod.GET_CUSTOMER_CATEGORIES`, `ADD_CUSTOMER_CATEGORY`, `REMOVE_CUSTOMER_CATEGORY`; `async _ManagerBase.get_customer_categories_api() -> CustomerCategoriesApi`

- [ ] **Step 1: Failing test**

```python
def test_customer_categories_methods_have_limits() -> None:
    """3 метода customer_categories есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "get_customer_categories": 1 / 60.0,
        "add_customer_category": 100 / 60.0,
        "remove_customer_category": 100 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация**

В `_base.py`: импорт `CustomerCategoriesApi` (алфавитно); в `ApiMethod` секция `# Customer Categories` с 3 значениями (`GET_CUSTOMER_CATEGORIES = "get_customer_categories"` и т.д.); 3 поля в `MethodRateLimits`; слот `_customer_categories_api: CustomerCategoriesApi | None` + геттер по паттерну соседних. В `api_client_manager.py.__init__`: слот + импорт. В `config_reader.py` (комментарий `# Customer Categories`): 3 поля по таблице лимитов. В `config.example.yml`: 3 блока.

- [ ] **Step 4: Run — PASS + качество**: unit +1, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/api_client_manager.py iikocloud/config_reader.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limits and lazy client for customer categories"
```

---

### Task 2: Core + helpers-заготовка + регистрация

**Files:**
- Create: `iikocloud/mixins/customer_categories/{__init__,core,helpers}.py`
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO + docstring)
- Test: `tests/unit/test_customer_categories.py`

**Interfaces:**
- Produces:
  - `get_customer_categories(request: GetCategoriesRequest) -> GetCategoriesResponse`
  - `add_customer_category(request: ChangeCategoryForCustomerRequest) -> None`
  - `remove_customer_category(request: ChangeCategoryForCustomerRequest) -> None`

- [ ] **Step 1: Failing tests**

`tests/unit/test_customer_categories.py`:

```python
"""Unit tests for CustomerCategories domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    ChangeCategoryForCustomerRequest,
    GetCategoriesRequest,
    GetCategoriesResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_customer_categories_api"


async def test_get_customer_categories_delegates() -> None:
    """get_customer_categories проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetCategoriesResponse)
    mock_api.get_customer_categories = AsyncMock(return_value=mock_response)

    request = GetCategoriesRequest(organization_id=ORG_ID)
    result = await manager.get_customer_categories(request)

    assert result is mock_response
    mock_api.get_customer_categories.assert_awaited_once_with(
        get_categories_request=request
    )


async def test_add_customer_category_returns_none() -> None:
    """add_customer_category: object-ответ -> None."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.add_customer_category = AsyncMock(return_value={})

    request = ChangeCategoryForCustomerRequest(
        category_id=ORG_ID, customer_id=ORG_ID, organization_id=ORG_ID
    )
    result = await manager.add_customer_category(request)

    assert result is None
    mock_api.add_customer_category.assert_awaited_once_with(
        change_category_for_customer_request=request
    )


async def test_remove_customer_category_returns_none() -> None:
    """remove_customer_category: object-ответ -> None."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.remove_customer_category = AsyncMock(return_value={})

    request = ChangeCategoryForCustomerRequest(
        category_id=ORG_ID, customer_id=ORG_ID, organization_id=ORG_ID
    )
    result = await manager.remove_customer_category(request)

    assert result is None
    mock_api.remove_customer_category.assert_awaited_once_with(
        change_category_for_customer_request=request
    )
```

- [ ] **Step 2: Run — FAIL** (AttributeError)

- [ ] **Step 3: Реализация**

`__init__.py` — реэкспорты обоих mixins по конвенции. `core.py`:

```python
"""CustomerCategories core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    ChangeCategoryForCustomerRequest,
    GetCategoriesRequest,
    GetCategoriesResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class CustomerCategoriesCoreMixin(_ManagerBase):
    """Core-методы CustomerCategories API."""

    async def get_customer_categories(
        self,
        request: GetCategoriesRequest,
    ) -> GetCategoriesResponse:
        """Все категории гостей организации."""

        async def api_call() -> GetCategoriesResponse:
            api = await self.get_customer_categories_api()
            return await api.get_customer_categories(
                get_categories_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_CUSTOMER_CATEGORIES, api_call
        )

    async def add_customer_category(
        self,
        request: ChangeCategoryForCustomerRequest,
    ) -> None:
        """Добавить категорию клиенту (object-ответ -> None)."""

        async def api_call() -> None:
            api = await self.get_customer_categories_api()
            await api.add_customer_category(
                change_category_for_customer_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_CUSTOMER_CATEGORY, api_call
        )

    async def remove_customer_category(
        self,
        request: ChangeCategoryForCustomerRequest,
    ) -> None:
        """Удалить категорию у клиента (object-ответ -> None)."""

        async def api_call() -> None:
            api = await self.get_customer_categories_api()
            await api.remove_customer_category(
                change_category_for_customer_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.REMOVE_CUSTOMER_CATEGORY, api_call
        )
```

`helpers.py` — заготовка `CustomerCategoriesHelpersMixin(CustomerCategoriesCoreMixin)` с docstring. В `api_client_manager.py`: импорт, MRO, docstring (`customer_categories`).

- [ ] **Step 4: Run — PASS + качество**: unit +3, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/customer_categories iikocloud/api_client_manager.py tests/unit/test_customer_categories.py
git commit -m "feat(customer-categories): get/add/remove category wrappers"
```

---

### Task 3: Integration (structure + danger_write цикл)

**Files:**
- Create: `tests/integration/customers/test_categories.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`; `generate_random_phone`; паттерн `_is_crm_unavailable` из `test_loyalty_write.py`

- [ ] **Step 1: Тест**

`tests/integration/customers/test_categories.py`:

```python
"""Интеграционные тесты CustomerCategories (write-секция).

structure-only: get_customer_categories (test_server).
danger_write: add -> remove на свежем тестовом клиенте (cleanup в finally).

Запуск:
    uv run pytest tests/integration/customers/test_categories.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    ChangeCategoryForCustomerRequest,
    CreateOrUpdateCustomerRequest,
    DeleteCustomersRequest,
    GetCategoriesRequest,
)
from iikocloud_client.exceptions import ApiException

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0


def _is_crm_unavailable(exc: BaseException) -> bool:
    body = getattr(exc, "body", None) or str(exc)
    return (
        "Transport_WrongCrmId" in body
        or "Common_OrganizationNotFound" in body
        or "Organization not found" in body
    )


class TestGetCustomerCategories:
    pytestmark = [
        pytest.mark.integration,
        pytest.mark.slow,
        pytest.mark.test_server,
        pytest.mark.asyncio(loop_scope="session"),
    ]

    async def test_get_customer_categories_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_customer_categories(
            GetCategoriesRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.guest_categories is not None


class TestCategoryLifecycle:
    pytestmark = [
        pytest.mark.integration,
        pytest.mark.slow,
        pytest.mark.danger_write,
        pytest.mark.asyncio(loop_scope="session"),
    ]

    async def test_add_and_remove_category(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        # category_id — первая активная категория стенда
        categories = await manager.get_customer_categories(
            GetCategoriesRequest(organization_id=organization_id)
        )
        active = [
            c
            for c in categories.guest_categories or []
            if c.is_active and c.id is not None
        ]
        if not active:
            pytest.skip("Нет активных категорий на write-стенде")
        category_id = active[0].id

        customer_id: UUID | None = None
        try:
            created = await manager.create_or_update_customer(
                CreateOrUpdateCustomerRequest(
                    organization_id=organization_id,
                    phone=generate_random_phone(),
                    name="Category Test",
                )
            )
            customer_id = created.id
            assert customer_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            try:
                await manager.add_customer_category(
                    ChangeCategoryForCustomerRequest(
                        category_id=category_id,
                        customer_id=customer_id,
                        organization_id=organization_id,
                    )
                )
                await asyncio.sleep(_API_PAUSE_SEC)
                await manager.remove_customer_category(
                    ChangeCategoryForCustomerRequest(
                        category_id=category_id,
                        customer_id=customer_id,
                        organization_id=organization_id,
                    )
                )
            except ApiException as exc:
                if _is_crm_unavailable(exc):
                    pytest.skip(f"Write-стенд без CRM: {exc}")
                raise
        finally:
            if customer_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.delete_customers(
                        DeleteCustomersRequest(
                            organization_id=organization_id,
                            customer_ids=[customer_id],
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Cleanup failed: %s", exc)
```

- [ ] **Step 2: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/customers/test_categories.py -q -rs`
Expected: PASS или skip с явной причиной (нет категорий/CRM).

- [ ] **Step 3: Регрессия + качество**: unit suite, ruff/mypy чисто
- [ ] **Step 4: Commit**

```bash
git add tests/integration/customers/test_categories.py
git commit -m "test: customer categories structure and add-remove lifecycle"
```
