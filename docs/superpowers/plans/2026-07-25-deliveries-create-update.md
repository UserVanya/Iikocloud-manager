# DeliveriesCreateAndUpdate Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обёртки над 20 методами `DeliveriesCreateAndUpdateApi` + 3 helpers + rate limits + unit- и danger_write-тесты.

**Architecture:** Новый домен `iikocloud/mixins/deliveries/` (`core.py` + `helpers.py`), регистрация через `DeliveriesHelpersMixin` в MRO `IikoCloudApiClientManager`. Core — тонкие обёртки через `execute_with_retry`, принимают SDK request-модель, возвращают SDK response (`None` для `update_delivery_tracking_link`).

**Tech Stack:** Python 3.12, `iikocloud_client` (git SDK @c0c810f), pydantic v2, pytest + pytest-asyncio, ruff + mypy (в dev-зависимостях).

**Spec:** `docs/superpowers/specs/2026-07-25-deliveries-create-update-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель (`request: XxxRequest`), возвращает SDK response или `None` для `update_delivery_tracking_link`.
- `ApiMethod` value == snake_case имени метода SDK == имя поля в `MethodRateLimitsSettings` и `MethodRateLimits` (Locked Names).
- Rate limits: `create_delivery_order` — 20/60s; остальные 19 команд — 100/60s.
- SDK kwargs подтверждены по коду SDK: `create_order_request`, `add_order_items_request`, `add_order_payments_request`, `cancel_order_request`, `cancel_delivery_confirmation_request`, `confirm_delivery_request`, `change_delivery_comment_request`, `change_complete_before_request`, `change_driver_info_request`, `change_external_data_request`, `change_delivery_operator_request`, `change_payments_request`, `change_delivery_point_request`, `change_service_type_request`, `close_delivery_order_request`, `print_delivery_bill_request`, `print_bill_request`, `update_order_problem_request`, `update_delivery_status_request`, `update_tracking_link_request`.
- `ChangeServiceTypeRequest.new_service_type` — обычная строка (`"DeliveryByCourier"` / `"DeliveryByClient"`); полиморфные подклассы `ChangeServiceTypeDeliveryBy*` этой моделью НЕ используются.
- Проверки качества после каждой задачи: `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`, `.venv/bin/python -m pytest tests/unit -q`.
- Integration: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/deliveries -q`.

---

### Task 1: Rate-limit инфраструктура + lazy API-клиент

**Files:**
- Modify: `iikocloud/mixins/_base.py` (ApiMethod, MethodRateLimits, импорт `DeliveriesCreateAndUpdateApi`, lazy-геттер)
- Modify: `iikocloud/config_reader.py` (`MethodRateLimitsSettings`)
- Modify: `config.example.yml` (`rate_limits`)
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces:
  - 20 значений `ApiMethod` (см. список ниже)
  - `MethodRateLimitsSettings.<locked_name>` с дефолтами
  - `MethodRateLimits` с 20 новыми полями
  - `async _ManagerBase.get_deliveries_create_and_update_api() -> DeliveriesCreateAndUpdateApi` (используется Task 2)

Список locked names (20): `create_delivery_order`, `add_delivery_order_items`, `add_delivery_order_payments`, `cancel_delivery_order`, `cancel_delivery_confirmation`, `confirm_delivery`, `change_delivery_comment`, `change_delivery_complete_before`, `change_delivery_driver_info`, `change_delivery_external_data`, `change_delivery_operator`, `change_delivery_payments`, `change_delivery_point`, `change_delivery_service_type`, `close_delivery_order`, `print_delivery_bill`, `print_table_order_bill`, `update_delivery_order_problem`, `update_delivery_order_status`, `update_delivery_tracking_link`.

- [ ] **Step 1: Failing test — locked names зарегистрированы**

Добавить в `tests/unit/test_config_reader.py`:

```python
def test_deliveries_methods_have_limits() -> None:
    """20 методов deliveries есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {"create_delivery_order": 20 / 60.0}
    commands = [
        "add_delivery_order_items",
        "add_delivery_order_payments",
        "cancel_delivery_order",
        "cancel_delivery_confirmation",
        "confirm_delivery",
        "change_delivery_comment",
        "change_delivery_complete_before",
        "change_delivery_driver_info",
        "change_delivery_external_data",
        "change_delivery_operator",
        "change_delivery_payments",
        "change_delivery_point",
        "change_delivery_service_type",
        "close_delivery_order",
        "print_delivery_bill",
        "print_table_order_bill",
        "update_delivery_order_problem",
        "update_delivery_order_status",
        "update_delivery_tracking_link",
    ]
    expected.update({name: 100 / 60.0 for name in commands})

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)
```

- [ ] **Step 2: Run — FAIL**

Run: `.venv/bin/python -m pytest tests/unit/test_config_reader.py::test_deliveries_methods_have_limits -q`
Expected: FAIL (`ValueError: 'create_delivery_order' is not a valid ApiMethod`)

- [ ] **Step 3: Реализация**

В `iikocloud/mixins/_base.py`:

1. Импорт: добавить `DeliveriesCreateAndUpdateApi` в импорт из `iikocloud_client` (алфавитный порядок).
2. В `ApiMethod` добавить секцию после dictionaries-блока:

```python
    # Deliveries (create & update)
    CREATE_DELIVERY_ORDER = "create_delivery_order"
    ADD_DELIVERY_ORDER_ITEMS = "add_delivery_order_items"
    ADD_DELIVERY_ORDER_PAYMENTS = "add_delivery_order_payments"
    CANCEL_DELIVERY_ORDER = "cancel_delivery_order"
    CANCEL_DELIVERY_CONFIRMATION = "cancel_delivery_confirmation"
    CONFIRM_DELIVERY = "confirm_delivery"
    CHANGE_DELIVERY_COMMENT = "change_delivery_comment"
    CHANGE_DELIVERY_COMPLETE_BEFORE = "change_delivery_complete_before"
    CHANGE_DELIVERY_DRIVER_INFO = "change_delivery_driver_info"
    CHANGE_DELIVERY_EXTERNAL_DATA = "change_delivery_external_data"
    CHANGE_DELIVERY_OPERATOR = "change_delivery_operator"
    CHANGE_DELIVERY_PAYMENTS = "change_delivery_payments"
    CHANGE_DELIVERY_POINT = "change_delivery_point"
    CHANGE_DELIVERY_SERVICE_TYPE = "change_delivery_service_type"
    CLOSE_DELIVERY_ORDER = "close_delivery_order"
    PRINT_DELIVERY_BILL = "print_delivery_bill"
    PRINT_TABLE_ORDER_BILL = "print_table_order_bill"
    UPDATE_DELIVERY_ORDER_PROBLEM = "update_delivery_order_problem"
    UPDATE_DELIVERY_ORDER_STATUS = "update_delivery_order_status"
    UPDATE_DELIVERY_TRACKING_LINK = "update_delivery_tracking_link"
```

3. В dataclass `MethodRateLimits` добавить 20 полей `RateLimitConfig` с теми же snake_case именами (после `get_tips_types`).
4. Объявление слота в `_ManagerBase` (рядом с `_dictionaries_api`):

```python
    _deliveries_create_and_update_api: DeliveriesCreateAndUpdateApi | None
```

5. Lazy-геттер (после `get_dictionaries_api`):

```python
    async def get_deliveries_create_and_update_api(
        self,
    ) -> DeliveriesCreateAndUpdateApi:
        """Получить клиент DeliveriesCreateAndUpdateApi."""
        await self._ensure_token_manager()
        if self._deliveries_create_and_update_api is None:
            self._deliveries_create_and_update_api = DeliveriesCreateAndUpdateApi(
                api_client=self._api_client
            )
        return self._deliveries_create_and_update_api
```

В `iikocloud/config_reader.py`, в `MethodRateLimitsSettings` после `get_tips_types` добавить (комментарий `# Deliveries (create & update)`):

```python
    create_delivery_order: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    add_delivery_order_items: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    add_delivery_order_payments: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    cancel_delivery_order: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    cancel_delivery_confirmation: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    confirm_delivery: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_comment: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_complete_before: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_driver_info: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_external_data: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_operator: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_payments: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_point: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_service_type: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    close_delivery_order: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    print_delivery_bill: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    print_table_order_bill: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    update_delivery_order_problem: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    update_delivery_order_status: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    update_delivery_tracking_link: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
```

В `config.example.yml` после блока `get_tips_types:` добавить 20 блоков (create — 20/60.0, остальные — 100/60.0), формат как у соседних.

ВНИМАНИЕ: `iikocloud/api_client_manager.py.__init__` тоже объявляет lazy-слоты (`self._dictionaries_api = None` и т.д.) — добавить туда же `self._deliveries_create_and_update_api = None` и импорт класса. (Иначе атрибут не будет инициализирован — слоты в `_ManagerBase` только аннотированы.)

- [ ] **Step 4: Run — PASS + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: 96 passed, ruff/mypy чисто

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/config_reader.py iikocloud/api_client_manager.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limits and lazy client for deliveries create/update"
```

---

### Task 2: Deliveries core — 20 обёрток

**Files:**
- Create: `iikocloud/mixins/deliveries/__init__.py` (пустой)
- Create: `iikocloud/mixins/deliveries/core.py`
- Test: `tests/unit/test_deliveries.py`

**Interfaces:**
- Consumes: `ApiMethod.*` и `get_deliveries_create_and_update_api()` (Task 1), `manager_with_stub_api("_deliveries_create_and_update_api")`
- Produces: `DeliveriesCoreMixin` с 20 методами (сигнатуры ниже — Task 3 наследует этот класс)

Минимальные request-модели для тестов (проверены конструированием в SDK; `u = ORG_ID`):

```python
AddOrderItemsRequest(organization_id=u, order_id=u, items=[])
AddOrderPaymentsRequest(organization_id=u, order_id=u, payments=[])
CancelOrderRequest(organization_id=u, order_id=u)
CancelDeliveryConfirmationRequest(organization_id=u, order_id=u)
ChangeDeliveryCommentRequest(organization_id=u, order_id=u, comment="c")
ChangeCompleteBeforeRequest(organization_id=u, order_id=u, new_complete_before="2026-07-26 12:00:00.000")
ChangeDriverInfoRequest(organization_id=u, order_id=u)
ChangeExternalDataRequest(organization_id=u, order_id=u, external_data=[])
ChangeDeliveryOperatorRequest(organization_id=u, order_id=u, operator_id=u)
ChangePaymentsRequest(organization_id=u, order_id=u, payments=[])
ChangeDeliveryPointRequest(organization_id=u, order_id=u, new_delivery_point=DeliveryOrderCreatePoint())
ChangeServiceTypeRequest(organization_id=u, order_id=u, new_service_type="DeliveryByCourier")
CloseDeliveryOrderRequest(organization_id=u, order_id=u)
ConfirmDeliveryRequest(organization_id=u, order_id=u)
PrintDeliveryBillRequest(organization_id=u, order_id=u)
PrintBillRequest(organization_id=u, order_id=u)
UpdateOrderProblemRequest(organization_id=u, order_id=u, has_problem=True)
UpdateDeliveryStatusRequest(organization_id=u, order_id=u, delivery_status=DeliveryStatusForUpdate.WAITING)
UpdateTrackingLinkRequest(organization_id=u, order_id=u, tracking_link="https://x")
CreateOrderRequest(organization_id=u, order=DeliveryOrder(phone="+79990001122", items=[DeliveryOrderCreateProductItem(type="Product", product_id=u, amount=1.0, price=1.0)]))
```

- [ ] **Step 1: Failing tests**

Создать `tests/unit/test_deliveries.py`:

```python
"""Unit tests for Deliveries domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    AddOrderItemsRequest,
    AddOrderPaymentsRequest,
    CancelDeliveryConfirmationRequest,
    CancelOrderRequest,
    ChangeCompleteBeforeRequest,
    ChangeDeliveryCommentRequest,
    ChangeDeliveryOperatorRequest,
    ChangeDeliveryPointRequest,
    ChangeExternalDataRequest,
    ChangeDriverInfoRequest,
    ChangePaymentsRequest,
    ChangeServiceTypeRequest,
    CloseDeliveryOrderRequest,
    ConfirmDeliveryRequest,
    CorrelationIdResponse,
    CreateOrderRequest,
    DeliveryOrder,
    DeliveryOrderCreatePoint,
    DeliveryOrderCreateProductItem,
    DeliveryStatusForUpdate,
    OrderResponse,
    PrintBillRequest,
    PrintDeliveryBillRequest,
    UpdateDeliveryStatusRequest,
    UpdateOrderProblemRequest,
    UpdateTrackingLinkRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_deliveries_create_and_update_api"

CORRELATION_METHODS = [
    ("add_delivery_order_items", AddOrderItemsRequest(organization_id=ORG_ID, order_id=ORG_ID, items=[]), "add_order_items_request"),
    ("add_delivery_order_payments", AddOrderPaymentsRequest(organization_id=ORG_ID, order_id=ORG_ID, payments=[]), "add_order_payments_request"),
    ("cancel_delivery_order", CancelOrderRequest(organization_id=ORG_ID, order_id=ORG_ID), "cancel_order_request"),
    ("cancel_delivery_confirmation", CancelDeliveryConfirmationRequest(organization_id=ORG_ID, order_id=ORG_ID), "cancel_delivery_confirmation_request"),
    ("confirm_delivery", ConfirmDeliveryRequest(organization_id=ORG_ID, order_id=ORG_ID), "confirm_delivery_request"),
    ("change_delivery_comment", ChangeDeliveryCommentRequest(organization_id=ORG_ID, order_id=ORG_ID, comment="c"), "change_delivery_comment_request"),
    ("change_delivery_complete_before", ChangeCompleteBeforeRequest(organization_id=ORG_ID, order_id=ORG_ID, new_complete_before="2026-07-26 12:00:00.000"), "change_complete_before_request"),
    ("change_delivery_driver_info", ChangeDriverInfoRequest(organization_id=ORG_ID, order_id=ORG_ID), "change_driver_info_request"),
    ("change_delivery_external_data", ChangeExternalDataRequest(organization_id=ORG_ID, order_id=ORG_ID, external_data=[]), "change_external_data_request"),
    ("change_delivery_operator", ChangeDeliveryOperatorRequest(organization_id=ORG_ID, order_id=ORG_ID, operator_id=ORG_ID), "change_delivery_operator_request"),
    ("change_delivery_payments", ChangePaymentsRequest(organization_id=ORG_ID, order_id=ORG_ID, payments=[]), "change_payments_request"),
    ("change_delivery_point", ChangeDeliveryPointRequest(organization_id=ORG_ID, order_id=ORG_ID, new_delivery_point=DeliveryOrderCreatePoint()), "change_delivery_point_request"),
    ("change_delivery_service_type", ChangeServiceTypeRequest(organization_id=ORG_ID, order_id=ORG_ID, new_service_type="DeliveryByCourier"), "change_service_type_request"),
    ("close_delivery_order", CloseDeliveryOrderRequest(organization_id=ORG_ID, order_id=ORG_ID), "close_delivery_order_request"),
    ("print_delivery_bill", PrintDeliveryBillRequest(organization_id=ORG_ID, order_id=ORG_ID), "print_delivery_bill_request"),
    ("print_table_order_bill", PrintBillRequest(organization_id=ORG_ID, order_id=ORG_ID), "print_bill_request"),
    ("update_delivery_order_problem", UpdateOrderProblemRequest(organization_id=ORG_ID, order_id=ORG_ID, has_problem=True), "update_order_problem_request"),
    ("update_delivery_order_status", UpdateDeliveryStatusRequest(organization_id=ORG_ID, order_id=ORG_ID, delivery_status=DeliveryStatusForUpdate.WAITING), "update_delivery_status_request"),
]


@pytest.mark.parametrize(
    ("method_name", "request", "sdk_kwarg"), CORRELATION_METHODS
)
async def test_correlation_methods_delegate(
    method_name: str, request: object, sdk_kwarg: str
) -> None:
    """Команды -> CorrelationIdResponse проксируются с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: request})


async def test_create_delivery_order_returns_order_response() -> None:
    """create_delivery_order проксирует OrderResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrderResponse)
    mock_api.create_delivery_order = AsyncMock(return_value=mock_response)

    request = CreateOrderRequest(
        organization_id=ORG_ID,
        order=DeliveryOrder(
            phone="+79990001122",
            items=[
                DeliveryOrderCreateProductItem(
                    type="Product", product_id=ORG_ID, amount=1.0, price=1.0
                )
            ],
        ),
    )
    result = await manager.create_delivery_order(request)

    assert result is mock_response
    mock_api.create_delivery_order.assert_awaited_once_with(
        create_order_request=request
    )


async def test_update_delivery_tracking_link_returns_none() -> None:
    """update_delivery_tracking_link: ответ без тела -> None."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.update_delivery_tracking_link = AsyncMock(return_value=None)

    request = UpdateTrackingLinkRequest(
        organization_id=ORG_ID, order_id=ORG_ID, tracking_link="https://x"
    )
    result = await manager.update_delivery_tracking_link(request)

    assert result is None
    mock_api.update_delivery_tracking_link.assert_awaited_once_with(
        update_tracking_link_request=request
    )
```

- [ ] **Step 2: Run — FAIL** (AttributeError: нет методов у менеджера)

- [ ] **Step 3: Реализация**

`iikocloud/mixins/deliveries/__init__.py` — пустой файл.

`iikocloud/mixins/deliveries/core.py`:

```python
"""Deliveries core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    AddOrderItemsRequest,
    AddOrderPaymentsRequest,
    CancelDeliveryConfirmationRequest,
    CancelOrderRequest,
    ChangeCompleteBeforeRequest,
    ChangeDeliveryCommentRequest,
    ChangeDeliveryOperatorRequest,
    ChangeDeliveryPointRequest,
    ChangeExternalDataRequest,
    ChangeDriverInfoRequest,
    ChangePaymentsRequest,
    ChangeServiceTypeRequest,
    CloseDeliveryOrderRequest,
    ConfirmDeliveryRequest,
    CorrelationIdResponse,
    CreateOrderRequest,
    OrderResponse,
    PrintBillRequest,
    PrintDeliveryBillRequest,
    UpdateDeliveryStatusRequest,
    UpdateOrderProblemRequest,
    UpdateTrackingLinkRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DeliveriesCoreMixin(_ManagerBase):
    """Core-методы Deliveries create & update API.

    Все методы, кроме create_delivery_order и update_delivery_tracking_link,
    — асинхронные команды: ответ CorrelationIdResponse, статус исполнения
    опрашивается через /api/1/commands/status.
    """

    async def create_delivery_order(
        self,
        request: CreateOrderRequest,
    ) -> OrderResponse:
        """Создать заказ доставки.

        Returns:
            OrderResponse с order_info.creation_status
            (Success / InProgress / Error)
        """

        async def api_call() -> OrderResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.create_delivery_order(create_order_request=request)

        return await self.execute_with_retry(
            ApiMethod.CREATE_DELIVERY_ORDER, api_call
        )

    async def add_delivery_order_items(
        self,
        request: AddOrderItemsRequest,
    ) -> CorrelationIdResponse:
        """Добавить позиции в заказ (iiko >= 7.4.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.add_delivery_order_items(
                add_order_items_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_DELIVERY_ORDER_ITEMS, api_call
        )

    async def add_delivery_order_payments(
        self,
        request: AddOrderPaymentsRequest,
    ) -> CorrelationIdResponse:
        """Добавить оплаты в заказ (iiko >= 8.4.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.add_delivery_order_payments(
                add_order_payments_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_DELIVERY_ORDER_PAYMENTS, api_call
        )

    async def cancel_delivery_order(
        self,
        request: CancelOrderRequest,
    ) -> CorrelationIdResponse:
        """Отменить заказ (статус Cancelled; заказ не удаляется физически)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.cancel_delivery_order(cancel_order_request=request)

        return await self.execute_with_retry(
            ApiMethod.CANCEL_DELIVERY_ORDER, api_call
        )

    async def cancel_delivery_confirmation(
        self,
        request: CancelDeliveryConfirmationRequest,
    ) -> CorrelationIdResponse:
        """Отменить подтверждение заказа (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.cancel_delivery_confirmation(
                cancel_delivery_confirmation_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_DELIVERY_CONFIRMATION, api_call
        )

    async def confirm_delivery(
        self,
        request: ConfirmDeliveryRequest,
    ) -> CorrelationIdResponse:
        """Подтвердить заказ (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.confirm_delivery(confirm_delivery_request=request)

        return await self.execute_with_retry(
            ApiMethod.CONFIRM_DELIVERY, api_call
        )

    async def change_delivery_comment(
        self,
        request: ChangeDeliveryCommentRequest,
    ) -> CorrelationIdResponse:
        """Изменить комментарий заказа."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_comment(
                change_delivery_comment_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_COMMENT, api_call
        )

    async def change_delivery_complete_before(
        self,
        request: ChangeCompleteBeforeRequest,
    ) -> CorrelationIdResponse:
        """Изменить время, к которому заказ должен быть готов."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_complete_before(
                change_complete_before_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_COMPLETE_BEFORE, api_call
        )

    async def change_delivery_driver_info(
        self,
        request: ChangeDriverInfoRequest,
    ) -> CorrelationIdResponse:
        """Изменить водителя/время доставки (iiko >= 8.6.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_driver_info(
                change_driver_info_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_DRIVER_INFO, api_call
        )

    async def change_delivery_external_data(
        self,
        request: ChangeExternalDataRequest,
    ) -> CorrelationIdResponse:
        """Изменить external data заказа."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_external_data(
                change_external_data_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_EXTERNAL_DATA, api_call
        )

    async def change_delivery_operator(
        self,
        request: ChangeDeliveryOperatorRequest,
    ) -> CorrelationIdResponse:
        """Изменить оператора заказа (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_operator(
                change_delivery_operator_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_OPERATOR, api_call
        )

    async def change_delivery_payments(
        self,
        request: ChangePaymentsRequest,
    ) -> CorrelationIdResponse:
        """Заменить все оплаты заказа (падает при processed payments)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_payments(
                change_payments_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_PAYMENTS, api_call
        )

    async def change_delivery_point(
        self,
        request: ChangeDeliveryPointRequest,
    ) -> CorrelationIdResponse:
        """Изменить точку доставки (адрес/координаты)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_point(
                change_delivery_point_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_POINT, api_call
        )

    async def change_delivery_service_type(
        self,
        request: ChangeServiceTypeRequest,
    ) -> CorrelationIdResponse:
        """Изменить тип сервиса (DeliveryByCourier / DeliveryByClient)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_service_type(
                change_service_type_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_SERVICE_TYPE, api_call
        )

    async def close_delivery_order(
        self,
        request: CloseDeliveryOrderRequest,
    ) -> CorrelationIdResponse:
        """Закрыть заказ (iiko >= 7.4.6; courier — только OnWay/Delivered с 8.0.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.close_delivery_order(
                close_delivery_order_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CLOSE_DELIVERY_ORDER, api_call
        )

    async def print_delivery_bill(
        self,
        request: PrintDeliveryBillRequest,
    ) -> CorrelationIdResponse:
        """Печать чека доставки (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.print_delivery_bill(
                print_delivery_bill_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.PRINT_DELIVERY_BILL, api_call
        )

    async def print_table_order_bill(
        self,
        request: PrintBillRequest,
    ) -> CorrelationIdResponse:
        """Печать чека столового заказа (endpoint /api/1/order/print_bill)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.print_table_order_bill(print_bill_request=request)

        return await self.execute_with_retry(
            ApiMethod.PRINT_TABLE_ORDER_BILL, api_call
        )

    async def update_delivery_order_problem(
        self,
        request: UpdateOrderProblemRequest,
    ) -> CorrelationIdResponse:
        """Установить/снять флаг проблемы заказа."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.update_delivery_order_problem(
                update_order_problem_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_DELIVERY_ORDER_PROBLEM, api_call
        )

    async def update_delivery_order_status(
        self,
        request: UpdateDeliveryStatusRequest,
    ) -> CorrelationIdResponse:
        """Изменить статус доставки (Waiting / OnWay / Delivered)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.update_delivery_order_status(
                update_delivery_status_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_DELIVERY_ORDER_STATUS, api_call
        )

    async def update_delivery_tracking_link(
        self,
        request: UpdateTrackingLinkRequest,
    ) -> None:
        """Обновить tracking-ссылку заказа (ответ без тела)."""

        async def api_call() -> None:
            api = await self.get_deliveries_create_and_update_api()
            await api.update_delivery_tracking_link(
                update_tracking_link_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_DELIVERY_TRACKING_LINK, api_call
        )
```

- [ ] **Step 4: Run — PASS + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: 116 passed, ruff/mypy чисто

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/deliveries tests/unit/test_deliveries.py
git commit -m "feat(deliveries): 20 core wrappers for create & update API"
```

---

### Task 3: Helpers + регистрация в менеджере

**Files:**
- Create: `iikocloud/mixins/deliveries/helpers.py`
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO)
- Test: `tests/unit/test_deliveries.py`

**Interfaces:**
- Consumes: `DeliveriesCoreMixin` (Task 2), `as_uuid` из `iikocloud/mixins/_base.py`
- Produces:
  - `DeliveriesHelpersMixin(DeliveriesCoreMixin)`:
    - `build_product_item(product_id: str | UUID, price: float, amount: float = 1.0, *, product_size_id: str | UUID | None = None, comment: str | None = None, modifiers: list[Modifier] | None = None) -> DeliveryOrderCreateProductItem`
    - `build_compound_item(primary_product_id: str | UUID, *, secondary_product_id: str | UUID | None = None, amount: float = 1.0, primary_price: float | None = None, secondary_price: float | None = None, common_modifiers: list[Modifier] | None = None, comment: str | None = None) -> DeliveryOrderCreateCompoundItem`
    - `cancel_order(organization_id: str | UUID, order_id: str | UUID, cancel_comment: str | None = None) -> CorrelationIdResponse`

- [ ] **Step 1: Failing tests**

Добавить в `tests/unit/test_deliveries.py` (импорты пополнить: `DeliveryOrderCreateCompoundItem`, `DeliveryOrderCreateCompoundItemComponent`, `Modifier`):

```python
def test_build_product_item_fills_discriminator() -> None:
    """build_product_item собирает Product-позицию с type='Product'."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    item = DeliveriesHelpersMixin.build_product_item(
        product_id=str(ORG_ID), price=150.0, amount=2.0, comment="no onion"
    )

    assert isinstance(item, DeliveryOrderCreateProductItem)
    assert item.type == "Product"
    assert item.product_id == ORG_ID
    assert item.price == 150.0
    assert item.amount == 2.0
    assert item.comment == "no onion"


def test_build_product_item_with_modifier() -> None:
    """build_product_item прокидывает modifiers."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    modifier = Modifier(product_id=ORG_ID, amount=1.0)
    item = DeliveriesHelpersMixin.build_product_item(
        product_id=ORG_ID, price=100.0, modifiers=[modifier]
    )

    assert item.modifiers == [modifier]


def test_build_compound_item_components() -> None:
    """build_compound_item собирает Compound-позицию с компонентами."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    item = DeliveriesHelpersMixin.build_compound_item(
        primary_product_id=ORG_ID,
        secondary_product_id=str(ORG_ID),
        primary_price=200.0,
    )

    assert isinstance(item, DeliveryOrderCreateCompoundItem)
    assert item.type == "Compound"
    assert isinstance(
        item.primary_component, DeliveryOrderCreateCompoundItemComponent
    )
    assert item.primary_component.product_id == ORG_ID
    assert item.primary_component.price == 200.0
    assert item.secondary_component is not None
    assert item.secondary_component.product_id == ORG_ID


def test_build_compound_item_without_secondary() -> None:
    """build_compound_item без второго компонента -> secondary=None."""
    from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin

    item = DeliveriesHelpersMixin.build_compound_item(primary_product_id=ORG_ID)

    assert item.secondary_component is None


async def test_cancel_order_builds_request() -> None:
    """cancel_order собирает CancelOrderRequest и вызывает core."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.cancel_delivery_order = AsyncMock(return_value=mock_response)

    result = await manager.cancel_order(
        organization_id=str(ORG_ID), order_id=ORG_ID, cancel_comment="test"
    )

    assert result is mock_response
    call_kwargs = mock_api.cancel_delivery_order.await_args.kwargs
    request = call_kwargs["cancel_order_request"]
    assert isinstance(request, CancelOrderRequest)
    assert request.organization_id == ORG_ID
    assert request.order_id == ORG_ID
    assert request.cancel_comment == "test"
```

Примечание: `build_*` — `@staticmethod` (не требуют экземпляра); `cancel_order` — обычный async-метод.

- [ ] **Step 2: Run — FAIL** (ModuleNotFoundError / AttributeError)

- [ ] **Step 3: Реализация**

`iikocloud/mixins/deliveries/helpers.py`:

```python
"""Deliveries helpers mixin — конструкторы позиций и короткие формы."""

from uuid import UUID

from iikocloud_client import (
    CancelOrderRequest,
    CorrelationIdResponse,
    DeliveryOrderCreateCompoundItem,
    DeliveryOrderCreateCompoundItemComponent,
    DeliveryOrderCreateProductItem,
    Modifier,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.deliveries.core import DeliveriesCoreMixin


class DeliveriesHelpersMixin(DeliveriesCoreMixin):
    """Публичный deliveries mixin с convenience-методами."""

    @staticmethod
    def build_product_item(
        product_id: str | UUID,
        price: float,
        amount: float = 1.0,
        *,
        product_size_id: str | UUID | None = None,
        comment: str | None = None,
        modifiers: list[Modifier] | None = None,
    ) -> DeliveryOrderCreateProductItem:
        """Собрать позицию-товар (дискриминатор type="Product").

        Args:
            product_id: ID продукта из номенклатуры
            price: Цена за единицу (обязательна в API)
            amount: Количество
            product_size_id: ID размера (для размерных товаров)
            comment: Комментарий к позиции
            modifiers: Модификаторы позиции
        """
        return DeliveryOrderCreateProductItem(
            type="Product",
            product_id=as_uuid(product_id),
            price=price,
            amount=amount,
            product_size_id=as_uuid(product_size_id) if product_size_id else None,
            comment=comment,
            modifiers=modifiers,
        )

    @staticmethod
    def build_compound_item(
        primary_product_id: str | UUID,
        *,
        secondary_product_id: str | UUID | None = None,
        amount: float = 1.0,
        primary_price: float | None = None,
        secondary_price: float | None = None,
        common_modifiers: list[Modifier] | None = None,
        comment: str | None = None,
    ) -> DeliveryOrderCreateCompoundItem:
        """Собрать составную позицию (дискриминатор type="Compound").

        Цена в API задаётся на уровне компонента (optional).
        """
        primary = DeliveryOrderCreateCompoundItemComponent(
            product_id=as_uuid(primary_product_id),
            price=primary_price,
        )
        secondary = (
            DeliveryOrderCreateCompoundItemComponent(
                product_id=as_uuid(secondary_product_id),
                price=secondary_price,
            )
            if secondary_product_id
            else None
        )
        return DeliveryOrderCreateCompoundItem(
            type="Compound",
            amount=amount,
            primary_component=primary,
            secondary_component=secondary,
            common_modifiers=common_modifiers,
            comment=comment,
        )

    async def cancel_order(
        self,
        organization_id: str | UUID,
        order_id: str | UUID,
        cancel_comment: str | None = None,
    ) -> CorrelationIdResponse:
        """Отменить заказ (короткая форма cancel_delivery_order)."""
        return await self.cancel_delivery_order(
            CancelOrderRequest(
                organization_id=as_uuid(organization_id),
                order_id=as_uuid(order_id),
                cancel_comment=cancel_comment,
            )
        )
```

В `iikocloud/api_client_manager.py`:
1. Импорт: `from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin`
2. В MRO класса добавить `DeliveriesHelpersMixin,` первым (перед `CustomersHelpersMixin`).
3. В docstring класса дополнить перечень доменов: `menu, dictionaries, deliveries`.

- [ ] **Step 4: Run — PASS + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: 121 passed, ruff/mypy чисто

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/deliveries/helpers.py iikocloud/api_client_manager.py tests/unit/test_deliveries.py
git commit -m "feat(deliveries): item builders and cancel_order helper, register in manager"
```

---

### Task 4: Integration danger_write — create → change → cancel

**Files:**
- Create: `tests/integration/deliveries/__init__.py` (пустой)
- Create: `tests/integration/deliveries/test_write.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`; helpers `build_product_item`, `cancel_order`; `generate_random_phone` из `tests/conftest.py`

- [ ] **Step 1: Тест**

`tests/integration/deliveries/test_write.py`:

```python
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
import pytest_asyncio
from iikocloud_client import (
    ChangeCompleteBeforeRequest,
    ChangeDeliveryCommentRequest,
    CreateOrderRequest,
    DeliveryOrder,
    NomenclatureRequest,
    TerminalGroupsIsAliveRequest,
    TerminalGroupsRequest,
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
```

- [ ] **Step 2: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/deliveries -q -rs`
Expected: PASS или skip с явной причиной (фронт офлайн / нет продуктов). Если create падает из-за отсутствия payments/delivery_point/order_service_type на стенде — зафиксировать ошибку в отчёте и добавить минимально необходимое поле (например `order_service_type="Common"`... — проверить фактическую причину, не гадать).

- [ ] **Step 3: Полный регрессионный прогон + качество**

Run: `.venv/bin/python -m pytest tests/unit -q && .venv/bin/ruff check . && .venv/bin/python -m mypy iikocloud tests`
Expected: unit 121 passed, ruff/mypy чисто

- [ ] **Step 4: Commit**

```bash
git add tests/integration/deliveries
git commit -m "test: danger_write delivery create-change-cancel lifecycle against write org"
```
