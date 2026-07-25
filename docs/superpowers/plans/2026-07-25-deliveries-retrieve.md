# DeliveriesRetrieve Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обёртки над 6 методами `DeliveriesRetrieveApi` + 2 helpers + клиентская валидация (200/XOR) + unit- и integration-тесты (read-back + structure-only).

**Architecture:** Новый домен `iikocloud/mixins/deliveries_retrieve/` (`core.py` + `helpers.py`), регистрация через `DeliveriesRetrieveHelpersMixin` в MRO. Core — тонкие обёртки через `execute_with_retry`, принимают SDK request-модель.

**Tech Stack:** Python 3.12, `iikocloud_client` (git SDK @c0c810f), pydantic v2, pytest + pytest-asyncio, ruff + mypy.

**Spec:** `docs/superpowers/specs/2026-07-25-deliveries-retrieve-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- `ApiMethod` value == snake_case имени метода SDK == имя поля в `MethodRateLimitsSettings` и `MethodRateLimits` (Locked Names).
- Rate limits: все 6 методов — 10/60s.
- SDK kwargs (проверены по коду SDK): `orders_by_delivery_date_and_phone_request`, `orders_by_delivery_date_and_status_request`, `orders_by_id_request`, `orders_by_revision_request`, `orders_history_by_delivery_date_and_phone_request`, `orders_by_delivery_date_and_filter_request`.
- Валидация до вызова SDK (ValueError):
  - `get_deliveries_by_id`: `order_ids` и `pos_order_ids` одновременно → ошибка; оба пусты/None → ошибка; len > 200 → ошибка.
  - `get_delivery_history_by_delivery_date_and_phone`: `rows_count > 200` или `< 1` → ошибка.
- `OrdersByDeliveryDateAndPhoneRequest.phone` — обязательный, но nullable (передавать явно `phone=None` при отсутствии фильтра).
- Проверки качества после каждой задачи: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.
- Integration: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/deliveries -q`.

---

### Task 1: Rate-limit инфраструктура + lazy API-клиент

**Files:**
- Modify: `iikocloud/mixins/_base.py` (ApiMethod, MethodRateLimits, импорт `DeliveriesRetrieveApi`, слот, lazy-геттер)
- Modify: `iikocloud/api_client_manager.py` (импорт, слот в `__init__`)
- Modify: `iikocloud/config_reader.py` (`MethodRateLimitsSettings`)
- Modify: `config.example.yml` (`rate_limits`)
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces:
  - 6 значений `ApiMethod`: `GET_DELIVERIES_BY_DELIVERY_DATE_AND_PHONE`, `GET_DELIVERIES_BY_DELIVERY_DATE_AND_STATUS`, `GET_DELIVERIES_BY_ID`, `GET_DELIVERIES_BY_REVISION`, `GET_DELIVERY_HISTORY_BY_DELIVERY_DATE_AND_PHONE`, `SEARCH_DELIVERIES`
  - `async _ManagerBase.get_deliveries_retrieve_api() -> DeliveriesRetrieveApi` (используется Task 2)

- [ ] **Step 1: Failing test**

Добавить в `tests/unit/test_config_reader.py`:

```python
def test_deliveries_retrieve_methods_have_limits() -> None:
    """6 методов deliveries_retrieve есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    names = [
        "get_deliveries_by_delivery_date_and_phone",
        "get_deliveries_by_delivery_date_and_status",
        "get_deliveries_by_id",
        "get_deliveries_by_revision",
        "get_delivery_history_by_delivery_date_and_phone",
        "search_deliveries",
    ]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            10 / 60.0
        )
```

- [ ] **Step 2: Run — FAIL** (`ValueError: ... is not a valid ApiMethod`)

- [ ] **Step 3: Реализация**

В `iikocloud/mixins/_base.py`:
1. Импорт `DeliveriesRetrieveApi` (алфавитно, после `DeliveriesCreateAndUpdateApi`).
2. В `ApiMethod` после deliveries-блока:

```python
    # Deliveries (retrieve)
    GET_DELIVERIES_BY_DELIVERY_DATE_AND_PHONE = (
        "get_deliveries_by_delivery_date_and_phone"
    )
    GET_DELIVERIES_BY_DELIVERY_DATE_AND_STATUS = (
        "get_deliveries_by_delivery_date_and_status"
    )
    GET_DELIVERIES_BY_ID = "get_deliveries_by_id"
    GET_DELIVERIES_BY_REVISION = "get_deliveries_by_revision"
    GET_DELIVERY_HISTORY_BY_DELIVERY_DATE_AND_PHONE = (
        "get_delivery_history_by_delivery_date_and_phone"
    )
    SEARCH_DELIVERIES = "search_deliveries"
```

3. В `MethodRateLimits` — 6 полей `RateLimitConfig` с теми же именами.
4. Слот: `_deliveries_retrieve_api: DeliveriesRetrieveApi | None` (рядом с `_deliveries_create_and_update_api`).
5. Lazy-геттер после `get_deliveries_create_and_update_api`:

```python
    async def get_deliveries_retrieve_api(self) -> DeliveriesRetrieveApi:
        """Получить клиент DeliveriesRetrieveApi."""
        await self._ensure_token_manager()
        if self._deliveries_retrieve_api is None:
            self._deliveries_retrieve_api = DeliveriesRetrieveApi(
                api_client=self._api_client
            )
        return self._deliveries_retrieve_api
```

В `iikocloud/api_client_manager.py.__init__`: `self._deliveries_retrieve_api = None` + импорт класса.

В `iikocloud/config_reader.py` после `update_delivery_tracking_link` (комментарий `# Deliveries (retrieve)`):

```python
    get_deliveries_by_delivery_date_and_phone: RateLimitSettings = (
        RateLimitSettings(max_requests=10, time_window_seconds=60.0)
    )
    get_deliveries_by_delivery_date_and_status: RateLimitSettings = (
        RateLimitSettings(max_requests=10, time_window_seconds=60.0)
    )
    get_deliveries_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_deliveries_by_revision: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_delivery_history_by_delivery_date_and_phone: RateLimitSettings = (
        RateLimitSettings(max_requests=10, time_window_seconds=60.0)
    )
    search_deliveries: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
```

В `config.example.yml` после блока `update_delivery_tracking_link:` — 6 блоков (10/60.0).

- [ ] **Step 4: Run — PASS + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: 122 passed, ruff/mypy чисто

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/config_reader.py iikocloud/api_client_manager.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limits and lazy client for deliveries retrieve"
```

---

### Task 2: DeliveriesRetrieve core — 6 обёрток + валидация

**Files:**
- Create: `iikocloud/mixins/deliveries_retrieve/__init__.py` (реэкспорт core;
  helpers-реэкспорт добавляется в Task 3)
- Create: `iikocloud/mixins/deliveries_retrieve/core.py`
- Test: `tests/unit/test_deliveries_retrieve.py`

**Interfaces:**
- Consumes: `ApiMethod.*`, `get_deliveries_retrieve_api()` (Task 1), `manager_with_stub_api("_deliveries_retrieve_api")`
- Produces: `DeliveriesRetrieveCoreMixin` с 6 методами:
  - `get_deliveries_by_delivery_date_and_phone(request) -> OrdersWithRevisionResponse`
  - `get_deliveries_by_delivery_date_and_status(request) -> OrdersWithRevisionResponse`
  - `get_deliveries_by_id(request) -> OrdersResponse` (+ валидация XOR/empty/200)
  - `get_deliveries_by_revision(request) -> OrdersWithRevisionResponse`
  - `get_delivery_history_by_delivery_date_and_phone(request) -> OrdersWithRevisionResponse` (+ валидация rows_count)
  - `search_deliveries(request) -> OrdersWithRevisionResponse`

Минимальные request-модели (проверены конструированием; `u = ORG_ID`):

```python
OrdersByDeliveryDateAndPhoneRequest(organization_ids=[u], phone=None)
OrdersByDeliveryDateAndStatusRequest(organization_ids=[u], delivery_date_from="2026-07-25 00:00:00.000")
OrdersByIdRequest(organization_id=u, order_ids=[u])
OrdersByRevisionRequest(organization_ids=[u], start_revision=0)
OrdersHistoryByDeliveryDateAndPhoneRequest(organization_ids=[u], phone="+7999", rows_count=10)
OrdersByDeliveryDateAndFilterRequest(organization_ids=[u])
```

- [ ] **Step 1: Failing tests**

Создать `tests/unit/test_deliveries_retrieve.py`:

```python
"""Unit tests for DeliveriesRetrieve domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    OrdersByDeliveryDateAndFilterRequest,
    OrdersByDeliveryDateAndPhoneRequest,
    OrdersByDeliveryDateAndStatusRequest,
    OrdersByIdRequest,
    OrdersByRevisionRequest,
    OrdersHistoryByDeliveryDateAndPhoneRequest,
    OrdersResponse,
    OrdersWithRevisionResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_deliveries_retrieve_api"

REVISION_METHODS = [
    (
        "get_deliveries_by_delivery_date_and_phone",
        OrdersByDeliveryDateAndPhoneRequest(
            organization_ids=[ORG_ID], phone=None
        ),
        "orders_by_delivery_date_and_phone_request",
    ),
    (
        "get_deliveries_by_delivery_date_and_status",
        OrdersByDeliveryDateAndStatusRequest(
            organization_ids=[ORG_ID],
            delivery_date_from="2026-07-25 00:00:00.000",
        ),
        "orders_by_delivery_date_and_status_request",
    ),
    (
        "get_deliveries_by_revision",
        OrdersByRevisionRequest(organization_ids=[ORG_ID], start_revision=0),
        "orders_by_revision_request",
    ),
    (
        "get_delivery_history_by_delivery_date_and_phone",
        OrdersHistoryByDeliveryDateAndPhoneRequest(
            organization_ids=[ORG_ID], phone="+7999", rows_count=10
        ),
        "orders_history_by_delivery_date_and_phone_request",
    ),
    (
        "search_deliveries",
        OrdersByDeliveryDateAndFilterRequest(organization_ids=[ORG_ID]),
        "orders_by_delivery_date_and_filter_request",
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg"), REVISION_METHODS
)
async def test_revision_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str
) -> None:
    """Методы -> OrdersWithRevisionResponse проксируются с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrdersWithRevisionResponse)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


async def test_get_deliveries_by_id_returns_orders_response() -> None:
    """get_deliveries_by_id проксирует плоский OrdersResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrdersResponse)
    mock_api.get_deliveries_by_id = AsyncMock(return_value=mock_response)

    request = OrdersByIdRequest(organization_id=ORG_ID, order_ids=[ORG_ID])
    result = await manager.get_deliveries_by_id(request)

    assert result is mock_response
    mock_api.get_deliveries_by_id.assert_awaited_once_with(
        orders_by_id_request=request
    )


async def test_get_deliveries_by_id_rejects_both_id_lists() -> None:
    """XOR: order_ids + pos_order_ids одновременно -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersByIdRequest(
        organization_id=ORG_ID, order_ids=[ORG_ID], pos_order_ids=[ORG_ID]
    )
    with pytest.raises(ValueError, match="order_ids"):
        await manager.get_deliveries_by_id(request)
    mock_api.get_deliveries_by_id.assert_not_called()


async def test_get_deliveries_by_id_rejects_empty() -> None:
    """Оба списка пусты/None -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersByIdRequest(organization_id=ORG_ID)
    with pytest.raises(ValueError, match="order_ids"):
        await manager.get_deliveries_by_id(request)
    mock_api.get_deliveries_by_id.assert_not_called()


async def test_get_deliveries_by_id_rejects_over_200() -> None:
    """> 200 id за запрос -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersByIdRequest(
        organization_id=ORG_ID, order_ids=[ORG_ID] * 201
    )
    with pytest.raises(ValueError, match="200"):
        await manager.get_deliveries_by_id(request)
    mock_api.get_deliveries_by_id.assert_not_called()


@pytest.mark.parametrize("rows_count", [0, 201])
async def test_history_rejects_bad_rows_count(rows_count: int) -> None:
    """rows_count вне 1..200 -> ValueError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = OrdersHistoryByDeliveryDateAndPhoneRequest(
        organization_ids=[ORG_ID], phone="+7999", rows_count=rows_count
    )
    with pytest.raises(ValueError, match="rows_count"):
        await manager.get_delivery_history_by_delivery_date_and_phone(request)
    mock_api.get_delivery_history_by_delivery_date_and_phone.assert_not_called()
```

Примечание: `OrdersByIdRequest(organization_id=ORG_ID)` без списков — оба поля optional в модели, сконструируется; валидация — наша.

- [ ] **Step 2: Run — FAIL** (AttributeError: нет методов)

- [ ] **Step 3: Реализация**

`iikocloud/mixins/deliveries_retrieve/__init__.py` (в Task 2 — только core;
импорт `.helpers` невозможен до Task 3, а `import ...deliveries_retrieve.core`
исполняет `__init__.py` пакета):

```python
"""DeliveriesRetrieve domain mixins."""

from iikocloud.mixins.deliveries_retrieve.core import DeliveriesRetrieveCoreMixin

__all__ = ["DeliveriesRetrieveCoreMixin"]
```

`iikocloud/mixins/deliveries_retrieve/core.py`:

```python
"""DeliveriesRetrieve core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    OrdersByDeliveryDateAndFilterRequest,
    OrdersByDeliveryDateAndPhoneRequest,
    OrdersByDeliveryDateAndStatusRequest,
    OrdersByIdRequest,
    OrdersByRevisionRequest,
    OrdersHistoryByDeliveryDateAndPhoneRequest,
    OrdersResponse,
    OrdersWithRevisionResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase

_MAX_IDS_PER_REQUEST = 200
_MAX_HISTORY_ROWS = 200


class DeliveriesRetrieveCoreMixin(_ManagerBase):
    """Core-методы Deliveries retrieve API (все read-only).

    Серверные ограничения домена: «горячие» заказы — последние 7 дней,
    история — 90 дней, revision-окно — 3 часа.
    """

    async def get_deliveries_by_delivery_date_and_phone(
        self,
        request: OrdersByDeliveryDateAndPhoneRequest,
    ) -> OrdersWithRevisionResponse:
        """Заказы по телефону/датам/revision (гарантия — последние 7 дней)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_delivery_date_and_phone(
                orders_by_delivery_date_and_phone_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_DELIVERY_DATE_AND_PHONE, api_call
        )

    async def get_deliveries_by_delivery_date_and_status(
        self,
        request: OrdersByDeliveryDateAndStatusRequest,
    ) -> OrdersWithRevisionResponse:
        """Заказы по статусам/датам/курьерам (гарантия — последние 7 дней)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_delivery_date_and_status(
                orders_by_delivery_date_and_status_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_DELIVERY_DATE_AND_STATUS, api_call
        )

    async def get_deliveries_by_id(
        self,
        request: OrdersByIdRequest,
    ) -> OrdersResponse:
        """Заказы по id (order_ids XOR pos_order_ids, максимум 200).

        Raises:
            ValueError: оба списка заданы, оба пусты или len > 200
        """
        self._validate_orders_by_id(request)

        async def api_call() -> OrdersResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_id(orders_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_ID, api_call
        )

    async def get_deliveries_by_revision(
        self,
        request: OrdersByRevisionRequest,
    ) -> OrdersWithRevisionResponse:
        """Изменённые заказы с ревизии (окно — 3 часа; инкрементальный поллинг)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_deliveries_by_revision(
                orders_by_revision_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERIES_BY_REVISION, api_call
        )

    async def get_delivery_history_by_delivery_date_and_phone(
        self,
        request: OrdersHistoryByDeliveryDateAndPhoneRequest,
    ) -> OrdersWithRevisionResponse:
        """История заказов по телефону (хранение 90 дней, rows_count <= 200).

        Raises:
            ValueError: rows_count вне 1..200
        """
        self._validate_history_rows(request)

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.get_delivery_history_by_delivery_date_and_phone(
                orders_history_by_delivery_date_and_phone_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERY_HISTORY_BY_DELIVERY_DATE_AND_PHONE, api_call
        )

    async def search_deliveries(
        self,
        request: OrdersByDeliveryDateAndFilterRequest,
    ) -> OrdersWithRevisionResponse:
        """Поиск заказов по тексту и фильтрам (статусы, проблема, сортировка)."""

        async def api_call() -> OrdersWithRevisionResponse:
            api = await self.get_deliveries_retrieve_api()
            return await api.search_deliveries(
                orders_by_delivery_date_and_filter_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.SEARCH_DELIVERIES, api_call
        )

    @staticmethod
    def _validate_orders_by_id(request: OrdersByIdRequest) -> None:
        """XOR + непустой + <= 200 id (иначе гарантированный 400 от API)."""
        order_ids = request.order_ids or []
        pos_order_ids = request.pos_order_ids or []
        if order_ids and pos_order_ids:
            raise ValueError(
                "order_ids и pos_order_ids взаимоисключающие (XOR) — "
                "задайте только один список"
            )
        if not order_ids and not pos_order_ids:
            raise ValueError(
                "Нужен непустой order_ids или pos_order_ids"
            )
        if len(order_ids) > _MAX_IDS_PER_REQUEST or (
            len(pos_order_ids) > _MAX_IDS_PER_REQUEST
        ):
            raise ValueError(
                f"Максимум {_MAX_IDS_PER_REQUEST} id за запрос"
            )

    @staticmethod
    def _validate_history_rows(
        request: OrdersHistoryByDeliveryDateAndPhoneRequest,
    ) -> None:
        """rows_count в 1..200 (иначе гарантированный 400 от API)."""
        if not 1 <= request.rows_count <= _MAX_HISTORY_ROWS:
            raise ValueError(
                f"rows_count должен быть в диапазоне 1..{_MAX_HISTORY_ROWS}"
            )
```

- [ ] **Step 4: Run — PASS + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: 131 passed, ruff/mypy чисто

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/deliveries_retrieve tests/unit/test_deliveries_retrieve.py
git commit -m "feat(deliveries-retrieve): 6 read wrappers with client-side 200/XOR validation"
```

---

### Task 3: Helpers + регистрация в менеджере

**Files:**
- Create: `iikocloud/mixins/deliveries_retrieve/helpers.py`
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO + docstring)
- Test: `tests/unit/test_deliveries_retrieve.py`

**Interfaces:**
- Consumes: `DeliveriesRetrieveCoreMixin` (Task 2), `as_uuid`
- Produces: `DeliveriesRetrieveHelpersMixin(DeliveriesRetrieveCoreMixin)`:
  - `async get_delivery_by_id(organization_id: str | UUID, order_id: str | UUID) -> OrderInfo | None`
  - `async get_customer_deliveries(organization_ids: list[str | UUID], phone: str, days: int = 7) -> list[OrderInfo]`

- [ ] **Step 1: Failing tests**

Добавить в `tests/unit/test_deliveries_retrieve.py` (импорты пополнить: `OrderInfo`):

```python
async def test_get_delivery_by_id_returns_first_order() -> None:
    """get_delivery_by_id возвращает единственный заказ из плоского ответа."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    order_info = MagicMock(spec=OrderInfo)
    mock_response = MagicMock(spec=OrdersResponse)
    mock_response.orders = [order_info]
    mock_api.get_deliveries_by_id = AsyncMock(return_value=mock_response)

    result = await manager.get_delivery_by_id(str(ORG_ID), ORG_ID)

    assert result is order_info
    call_kwargs = mock_api.get_deliveries_by_id.await_args.kwargs
    request = call_kwargs["orders_by_id_request"]
    assert isinstance(request, OrdersByIdRequest)
    assert request.organization_id == ORG_ID
    assert request.order_ids == [ORG_ID]


async def test_get_delivery_by_id_returns_none_when_missing() -> None:
    """get_delivery_by_id -> None, если заказ не найден."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrdersResponse)
    mock_response.orders = []
    mock_api.get_deliveries_by_id = AsyncMock(return_value=mock_response)

    result = await manager.get_delivery_by_id(ORG_ID, ORG_ID)

    assert result is None


async def test_get_customer_deliveries_builds_date_window() -> None:
    """get_customer_deliveries собирает период и выравнивает ответ."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    order_info = MagicMock(spec=OrderInfo)
    org_orders = MagicMock()
    org_orders.orders = [order_info]
    mock_response = MagicMock(spec=OrdersWithRevisionResponse)
    mock_response.orders_by_organizations = [org_orders]
    mock_api.get_deliveries_by_delivery_date_and_phone = AsyncMock(
        return_value=mock_response
    )

    result = await manager.get_customer_deliveries(
        [str(ORG_ID)], phone="+79990001122", days=3
    )

    assert result == [order_info]
    call_kwargs = (
        mock_api.get_deliveries_by_delivery_date_and_phone.await_args.kwargs
    )
    request = call_kwargs["orders_by_delivery_date_and_phone_request"]
    assert isinstance(request, OrdersByDeliveryDateAndPhoneRequest)
    assert request.organization_ids == [ORG_ID]
    assert request.phone == "+79990001122"
    # delivery_date_from заполнен и раньше delivery_date_to
    assert request.delivery_date_from is not None
    assert request.delivery_date_to is not None
    assert request.delivery_date_from < request.delivery_date_to
```

- [ ] **Step 2: Run — FAIL** (AttributeError/ModuleNotFoundError)

- [ ] **Step 3: Реализация**

`iikocloud/mixins/deliveries_retrieve/helpers.py`:

```python
"""DeliveriesRetrieve helpers mixin — короткие формы чтения заказов."""

from datetime import datetime, timedelta
from uuid import UUID

from iikocloud_client import (
    OrderInfo,
    OrdersByDeliveryDateAndPhoneRequest,
    OrdersByIdRequest,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.deliveries_retrieve.core import (
    DeliveriesRetrieveCoreMixin,
)

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.000"


class DeliveriesRetrieveHelpersMixin(DeliveriesRetrieveCoreMixin):
    """Публичный deliveries-retrieve mixin с convenience-методами."""

    async def get_delivery_by_id(
        self,
        organization_id: str | UUID,
        order_id: str | UUID,
    ) -> OrderInfo | None:
        """Один заказ по id (None, если не найден)."""
        response = await self.get_deliveries_by_id(
            OrdersByIdRequest(
                organization_id=as_uuid(organization_id),
                order_ids=[as_uuid(order_id)],
            )
        )
        orders = response.orders or []
        return orders[0] if orders else None

    async def get_customer_deliveries(
        self,
        organization_ids: list[str | UUID],
        phone: str,
        days: int = 7,
    ) -> list[OrderInfo]:
        """Заказы клиента по телефону за последние N дней (плоский список).

        Даты — локальное время терминала (гарантия доступности — 7 дней).
        """
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)
        response = await self.get_deliveries_by_delivery_date_and_phone(
            OrdersByDeliveryDateAndPhoneRequest(
                organization_ids=[as_uuid(oid) for oid in organization_ids],
                phone=phone,
                delivery_date_from=date_from.strftime(_DATE_FORMAT),
                delivery_date_to=date_to.strftime(_DATE_FORMAT),
            )
        )
        return [
            order
            for org_orders in response.orders_by_organizations or []
            for order in org_orders.orders or []
        ]
```

В `iikocloud/api_client_manager.py`:
1. Импорт: `from iikocloud.mixins.deliveries_retrieve.helpers import DeliveriesRetrieveHelpersMixin`
2. В MRO добавить `DeliveriesRetrieveHelpersMixin,` (после `DeliveriesHelpersMixin,`).
3. Docstring: `menu, dictionaries, deliveries, deliveries_retrieve.`

В `iikocloud/mixins/deliveries_retrieve/__init__.py` добавить helpers-реэкспорт
(итоговый файл):

```python
"""DeliveriesRetrieve domain mixins."""

from iikocloud.mixins.deliveries_retrieve.core import DeliveriesRetrieveCoreMixin
from iikocloud.mixins.deliveries_retrieve.helpers import (
    DeliveriesRetrieveHelpersMixin,
)

__all__ = ["DeliveriesRetrieveCoreMixin", "DeliveriesRetrieveHelpersMixin"]
```

- [ ] **Step 4: Run — PASS + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: 134 passed, ruff/mypy чисто

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/deliveries_retrieve/helpers.py iikocloud/api_client_manager.py tests/unit/test_deliveries_retrieve.py
git commit -m "feat(deliveries-retrieve): get_delivery_by_id and get_customer_deliveries helpers"
```

---

### Task 4: Integration — read-back danger_write + structure-only

**Files:**
- Create: `tests/integration/deliveries/test_read.py`
- Create: `tests/integration/deliveries/test_read_structure.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`; фикстуры/паттерны из `tests/integration/deliveries/test_write.py` (`live_terminal_group_id`, `product`, create-заказа); helpers `get_delivery_by_id`, `build_product_item`, `cancel_order`; `generate_random_phone`

- [ ] **Step 1: Read-back тест**

`tests/integration/deliveries/test_read.py`:

```python
"""Read-back danger_write-тест DeliveriesRetrieve (write-секция).

create -> get_delivery_by_id -> search_deliveries по телефону -> cancel.
Проверяет, что созданный заказ реально читается retrieve-методами.

Запуск:
    uv run pytest tests/integration/deliveries/test_read.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
import pytest_asyncio
from iikocloud_client import (
    CreateOrderRequest,
    DeliveryOrder,
    OrdersByDeliveryDateAndFilterRequest,
)

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone
from tests.integration.deliveries.test_write import (
    live_terminal_group_id,  # noqa: F401  (переиспользуем фикстуры)
    product,  # noqa: F401
)

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0
_READBACK_ATTEMPTS = 5
_READBACK_INTERVAL_SEC = 2.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestDeliveryReadback:
    async def test_created_order_is_readable(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, price = product
        phone = generate_random_phone()
        order_id: UUID | None = None
        try:
            # 1. create
            item = manager.build_product_item(product_id=product_id, price=price)
            create_response = await manager.create_delivery_order(
                CreateOrderRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    order=DeliveryOrder(
                        phone=phone,
                        items=[item],
                        order_service_type="DeliveryByClient",
                    ),
                )
            )
            order_info = create_response.order_info
            assert order_info is not None
            status_value = getattr(order_info.creation_status, "value", None)
            assert status_value != "Error", f"Create failed: {order_info.error_info}"
            order_id = order_info.id
            assert order_id is not None

            # 2. get_delivery_by_id (bounded-поллинг: индексация не мгновенная)
            found = None
            for _ in range(_READBACK_ATTEMPTS):
                await asyncio.sleep(_READBACK_INTERVAL_SEC)
                found = await manager.get_delivery_by_id(organization_id, order_id)
                if found is not None:
                    break
            assert found is not None, "Заказ не появился в get_deliveries_by_id"
            assert found.id == order_id

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. search_deliveries по телефону
            found_by_phone = []
            for _ in range(_READBACK_ATTEMPTS):
                await asyncio.sleep(_READBACK_INTERVAL_SEC)
                search_response = await manager.search_deliveries(
                    OrdersByDeliveryDateAndFilterRequest(
                        organization_ids=[organization_id],
                        search_text=phone,
                    )
                )
                found_by_phone = [
                    order
                    for org_orders in search_response.orders_by_organizations or []
                    for order in org_orders.orders or []
                    if order.id == order_id
                ]
                if found_by_phone:
                    break
            assert found_by_phone, "Заказ не найден через search_deliveries"

        finally:
            # 4. cleanup: cancel
            if order_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_order(
                        organization_id=organization_id,
                        order_id=order_id,
                        cancel_comment="integration read-back cleanup",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Cancel cleanup failed for order %s: %s", order_id, exc
                    )
```

ВНИМАНИЕ: импорт фикстур из `test_write.py` — рабочий pytest-паттерн (импортированная фикстура регистрируется в модуле). Если ruff/mypy возражает — перенести фикстуры `live_terminal_group_id`/`product` в `tests/integration/deliveries/conftest.py` и убрать из test_write.py (предпочтительный вариант — сделай так, если есть хоть одна проблема с импортом).

- [ ] **Step 2: Structure-only тесты**

`tests/integration/deliveries/test_read_structure.py`:

```python
"""Structure-only read-тесты DeliveriesRetrieve (write-секция через test_server).

Проверяем вызов + структуру ответа без привязки к данным стенда.

Запуск:
    uv run pytest tests/integration/deliveries/test_read_structure.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from iikocloud_client import (
    DeliveryStatus,
    OrdersByDeliveryDateAndPhoneRequest,
    OrdersByDeliveryDateAndStatusRequest,
    OrdersByRevisionRequest,
    OrdersHistoryByDeliveryDateAndPhoneRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.000"


class TestRetrieveStructure:
    async def test_by_delivery_date_and_phone(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_deliveries_by_delivery_date_and_phone(
            OrdersByDeliveryDateAndPhoneRequest(
                organization_ids=[organization_id],
                phone=None,
                delivery_date_from=(datetime.now() - timedelta(days=1)).strftime(
                    _DATE_FORMAT
                ),
            )
        )
        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.orders_by_organizations is not None

    async def test_by_delivery_date_and_status(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_deliveries_by_delivery_date_and_status(
            OrdersByDeliveryDateAndStatusRequest(
                organization_ids=[organization_id],
                delivery_date_from=(datetime.now() - timedelta(days=1)).strftime(
                    _DATE_FORMAT
                ),
                statuses=[DeliveryStatus.CANCELLED],
            )
        )
        assert response is not None
        assert response.orders_by_organizations is not None

    async def test_by_revision(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """start_revision=0: стенд может отклонить окно > 3ч — тогда skip."""
        from iikocloud_client.exceptions import ApiException

        try:
            response = await manager.get_deliveries_by_revision(
                OrdersByRevisionRequest(
                    organization_ids=[organization_id], start_revision=0
                )
            )
        except ApiException as exc:
            pytest.skip(f"Стенд отклонил start_revision=0 (окно 3ч): {exc}")
        assert response is not None
        assert response.orders_by_organizations is not None
        assert isinstance(response.max_revision, int)

    async def test_history_by_phone(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_delivery_history_by_delivery_date_and_phone(
            OrdersHistoryByDeliveryDateAndPhoneRequest(
                organization_ids=[organization_id],
                phone="+70000000000",
                rows_count=10,
            )
        )
        assert response is not None
        assert response.orders_by_organizations is not None
```

Проверить при реализации: `DeliveryStatus.CANCELLED` — имя члена enum (ожидается `Cancelled` → член `CANCELLED`; сверить с моделью SDK).

- [ ] **Step 3: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/deliveries -q -rs`
Expected: все PASS (включая ранее существующий test_write) или skip с явной причиной.

- [ ] **Step 4: Регрессия + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: unit 134 passed, ruff/mypy чисто

- [ ] **Step 5: Commit**

```bash
git add tests/integration/deliveries
git commit -m "test: deliveries retrieve read-back and structure-only integration tests"
```
