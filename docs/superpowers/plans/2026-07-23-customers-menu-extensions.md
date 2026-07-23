# Customers+/Menu+ Extensions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить 8 методов `CustomersApi` и 7 методов `MenuApi` в mixins менеджера с rate limits, unit- и real API-тестами.

**Architecture:** Core-методы — тонкие async-обёртки над SDK через `execute_with_retry`, принимают SDK request-модель целиком и возвращают SDK response-модель (`None` для `object`-ответов). Лимиты — через `ApiMethod` (Locked Names) + `MethodRateLimitsSettings`. Helpers не добавляются.

**Tech Stack:** Python 3.12, `iikocloud_client` (git SDK), pydantic v2, pytest + pytest-asyncio, запуск через `.venv/bin/python -m pytest`.

**Spec:** `docs/superpowers/specs/2026-07-23-customers-menu-extensions-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель (`request: XxxRequest`), возвращает SDK response или `None` для `object`-ответов.
- `ApiMethod` value == snake_case имени метода SDK == имя поля в `MethodRateLimitsSettings` и `MethodRateLimits` (Locked Names).
- Все новые SDK-модели импортируются из корня `iikocloud_client` (проверено: все 28 имён экспортируются).
- `top_up_customer_balance` / `withdraw_customer_balance`: `customer_id` и `wallet_id` обязательны — ValueError до вызова SDK.
- Маркер write-тестов: `danger_write` (новый), роутится на write-секцию `config.test.yml`.
- Rate limits (из спеки): customers write — 100/60s; `get_loyalty_counters` — 10/60s; stop-list мутации — 1/60s; `check_products_in_stop_list` — 10/60s; `get_nomenclature` — 1/60s; `get_combos_info`, `calculate_combo_price` — 10/60s.
- Прогон unit: `.venv/bin/python -m pytest tests/unit -q`. Прогон integration: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration -q`.

---

### Task 1: Rate-limit инфраструктура (ApiMethod, settings, config.example.yml)

**Files:**
- Modify: `iikocloud/mixins/_base.py:56-86` (enum `ApiMethod`), `iikocloud/mixins/_base.py:111-132` (dataclass `MethodRateLimits`)
- Modify: `iikocloud/config_reader.py:45-116` (`MethodRateLimitsSettings`)
- Modify: `config.example.yml` (секция `rate_limits`)
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces (используется Tasks 2-6):
  - `ApiMethod.ADD_CUSTOMER_MAGNET_CARD` … `ApiMethod.CALCULATE_COMBO_PRICE` — 15 значений
  - `MethodRateLimitsSettings.<locked_name>` с дефолтами
  - `MethodRateLimits` с 15 новыми полями `RateLimitConfig`

- [ ] **Step 1: Failing test — locked names зарегистрированы и имеют лимиты**

Добавить в `tests/unit/test_config_reader.py`:

```python
def test_new_extension_methods_have_limits() -> None:
    """15 новых методов customers+/menu+ есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "add_customer_magnet_card": 100 / 60.0,
        "remove_customer_magnet_card": 100 / 60.0,
        "add_customer_to_program": 100 / 60.0,
        "hold_customer_balance": 100 / 60.0,
        "cancel_customer_balance_hold": 100 / 60.0,
        "top_up_customer_balance": 100 / 60.0,
        "withdraw_customer_balance": 100 / 60.0,
        "get_loyalty_counters": 10 / 60.0,
        "add_products_to_stop_list": 1 / 60.0,
        "remove_products_from_stop_list": 1 / 60.0,
        "clear_stop_list": 1 / 60.0,
        "check_products_in_stop_list": 10 / 60.0,
        "get_nomenclature": 1 / 60.0,
        "get_combos_info": 10 / 60.0,
        "calculate_combo_price": 10 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        method = ApiMethod(name)
        config = limits.for_method(method)
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)
```

(файл уже импортирует `pytest` и `MethodRateLimitsSettings` — проверить импорты в начале файла и при необходимости добавить.)

- [ ] **Step 2: Run — FAIL**

Run: `.venv/bin/python -m pytest tests/unit/test_config_reader.py::test_new_extension_methods_have_limits -q`
Expected: FAIL (`ValueError: 'add_customer_magnet_card' is not a valid ApiMethod`)

- [ ] **Step 3: Реализация**

В `iikocloud/mixins/_base.py`, в `ApiMethod` после `RESTORE_CUSTOMERS` добавить:

```python
    ADD_CUSTOMER_MAGNET_CARD = "add_customer_magnet_card"
    REMOVE_CUSTOMER_MAGNET_CARD = "remove_customer_magnet_card"
    ADD_CUSTOMER_TO_PROGRAM = "add_customer_to_program"
    HOLD_CUSTOMER_BALANCE = "hold_customer_balance"
    CANCEL_CUSTOMER_BALANCE_HOLD = "cancel_customer_balance_hold"
    TOP_UP_CUSTOMER_BALANCE = "top_up_customer_balance"
    WITHDRAW_CUSTOMER_BALANCE = "withdraw_customer_balance"
    GET_LOYALTY_COUNTERS = "get_loyalty_counters"
```

В `ApiMethod` после `GET_STOP_LISTS` добавить:

```python
    ADD_PRODUCTS_TO_STOP_LIST = "add_products_to_stop_list"
    REMOVE_PRODUCTS_FROM_STOP_LIST = "remove_products_from_stop_list"
    CLEAR_STOP_LIST = "clear_stop_list"
    CHECK_PRODUCTS_IN_STOP_LIST = "check_products_in_stop_list"
    GET_NOMENCLATURE = "get_nomenclature"
    GET_COMBOS_INFO = "get_combos_info"
    CALCULATE_COMBO_PRICE = "calculate_combo_price"
```

В dataclass `MethodRateLimits` (там же, после `restore_customers: RateLimitConfig` и `get_stop_lists: RateLimitConfig` соответственно) добавить 15 полей с теми же именами:

```python
    add_customer_magnet_card: RateLimitConfig
    remove_customer_magnet_card: RateLimitConfig
    add_customer_to_program: RateLimitConfig
    hold_customer_balance: RateLimitConfig
    cancel_customer_balance_hold: RateLimitConfig
    top_up_customer_balance: RateLimitConfig
    withdraw_customer_balance: RateLimitConfig
    get_loyalty_counters: RateLimitConfig
    add_products_to_stop_list: RateLimitConfig
    remove_products_from_stop_list: RateLimitConfig
    clear_stop_list: RateLimitConfig
    check_products_in_stop_list: RateLimitConfig
    get_nomenclature: RateLimitConfig
    get_combos_info: RateLimitConfig
    calculate_combo_price: RateLimitConfig
```

В `iikocloud/config_reader.py`, в `MethodRateLimitsSettings` после `restore_customers` добавить (комментарий `# Customers — cards / programs / wallets`):

```python
    add_customer_magnet_card: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    remove_customer_magnet_card: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    add_customer_to_program: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    hold_customer_balance: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    cancel_customer_balance_hold: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    top_up_customer_balance: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    withdraw_customer_balance: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    get_loyalty_counters: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
```

После `get_stop_lists` добавить (комментарий `# Menu — stop lists / nomenclature / combos`):

```python
    add_products_to_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    remove_products_from_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    clear_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    check_products_in_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_nomenclature: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_combos_info: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    calculate_combo_price: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
```

В `config.example.yml` после блока `restore_customers:` добавить 8 блоков (100/60.0 для всех, кроме `get_loyalty_counters` — 10/60.0), после блока `get_stop_lists:` — 7 блоков по таблице выше. Формат блока:

```yaml
    add_customer_magnet_card:
      max_requests: 100
      time_window_seconds: 60.0
```

- [ ] **Step 4: Run — PASS**

Run: `.venv/bin/python -m pytest tests/unit -q`
Expected: все PASS (включая существующие 77 + новый)

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/config_reader.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limits for customers+/menu+ extension methods"
```

---

### Task 2: Customers core — карты и программа лояльности

**Files:**
- Modify: `iikocloud/mixins/customers/core.py`
- Test: `tests/unit/test_customers.py`

**Interfaces:**
- Consumes: `ApiMethod.ADD_CUSTOMER_MAGNET_CARD` и др. (Task 1), `manager_with_stub_api("_customers_api")` из `tests/unit/conftest.py`
- Produces:
  - `async CustomersCoreMixin.add_customer_magnet_card(request: AddMagnetCardRequest) -> None`
  - `async CustomersCoreMixin.remove_customer_magnet_card(request: DeleteMagnetCardRequest) -> None`
  - `async CustomersCoreMixin.add_customer_to_program(request: AddCustomerToProgramRequest) -> AddCustomerToProgramResponse`

- [ ] **Step 1: Failing tests**

Добавить в `tests/unit/test_customers.py` (импорты пополнить: `AddMagnetCardRequest`, `DeleteMagnetCardRequest`, `AddCustomerToProgramRequest`, `AddCustomerToProgramResponse`):

```python
async def test_add_customer_magnet_card_calls_api() -> None:
    """add_customer_magnet_card delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.add_customer_magnet_card = AsyncMock(return_value={})

    request = AddMagnetCardRequest(
        card_number="123456",
        card_track="track-1",
        customer_id=ORG_ID,
        organization_id=ORG_ID,
    )
    result = await manager.add_customer_magnet_card(request)

    assert result is None
    mock_api.add_customer_magnet_card.assert_awaited_once_with(
        add_magnet_card_request=request
    )


async def test_remove_customer_magnet_card_calls_api() -> None:
    """remove_customer_magnet_card delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.remove_customer_magnet_card = AsyncMock(return_value={})

    request = DeleteMagnetCardRequest(
        card_track="track-1",
        customer_id=ORG_ID,
        organization_id=ORG_ID,
    )
    result = await manager.remove_customer_magnet_card(request)

    assert result is None
    mock_api.remove_customer_magnet_card.assert_awaited_once_with(
        delete_magnet_card_request=request
    )


async def test_add_customer_to_program_returns_response() -> None:
    """add_customer_to_program proxies AddCustomerToProgramResponse."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_response = MagicMock(spec=AddCustomerToProgramResponse)
    mock_api.add_customer_to_program = AsyncMock(return_value=mock_response)

    request = AddCustomerToProgramRequest(
        customer_id=ORG_ID,
        organization_id=ORG_ID,
        program_id=ORG_ID,
    )
    result = await manager.add_customer_to_program(request)

    assert result is mock_response
    mock_api.add_customer_to_program.assert_awaited_once_with(
        add_customer_to_program_request=request
    )
```

(`ORG_ID` уже определён в файле; если нет — `ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")`.)

- [ ] **Step 2: Run — FAIL** (AttributeError: нет метода у менеджера)

Run: `.venv/bin/python -m pytest tests/unit/test_customers.py -q -k magnet_card or -k program`

- [ ] **Step 3: Реализация**

В `iikocloud/mixins/customers/core.py` пополнить импорты:

```python
from iikocloud_client import (
    AddCustomerToProgramRequest,
    AddCustomerToProgramResponse,
    AddMagnetCardRequest,
    DeleteMagnetCardRequest,
    # ... существующие импорты оставить
)
```

Добавить в `CustomersCoreMixin`:

```python
    async def add_customer_magnet_card(
        self,
        request: AddMagnetCardRequest,
    ) -> None:
        """Привязать магнитную карту к клиенту.

        Args:
            request: cardNumber, cardTrack, customerId, organizationId
        """

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.add_customer_magnet_card(add_magnet_card_request=request)

        return await self.execute_with_retry(
            ApiMethod.ADD_CUSTOMER_MAGNET_CARD, api_call
        )

    async def remove_customer_magnet_card(
        self,
        request: DeleteMagnetCardRequest,
    ) -> None:
        """Отвязать магнитную карту от клиента.

        Args:
            request: cardTrack, customerId, organizationId
        """

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.remove_customer_magnet_card(
                delete_magnet_card_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.REMOVE_CUSTOMER_MAGNET_CARD, api_call
        )

    async def add_customer_to_program(
        self,
        request: AddCustomerToProgramRequest,
    ) -> AddCustomerToProgramResponse:
        """Добавить клиента в программу лояльности.

        Args:
            request: customerId, organizationId, programId

        Returns:
            Ответ с userWalletId/walletId кошелька программы
        """

        async def api_call() -> AddCustomerToProgramResponse:
            api = await self.get_customers_api()
            return await api.add_customer_to_program(
                add_customer_to_program_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_CUSTOMER_TO_PROGRAM, api_call
        )
```

- [ ] **Step 4: Run — PASS**: `.venv/bin/python -m pytest tests/unit/test_customers.py -q`

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/customers/core.py tests/unit/test_customers.py
git commit -m "feat(customers): magnet card add/remove and add-to-program wrappers"
```

---

### Task 3: Customers core — баланс (hold/cancel/topup/withdraw)

**Files:**
- Modify: `iikocloud/mixins/customers/core.py`
- Test: `tests/unit/test_customers.py`

**Interfaces:**
- Produces:
  - `async CustomersCoreMixin.hold_customer_balance(request: HoldMoneyRequest) -> HoldMoneyResponse`
  - `async CustomersCoreMixin.cancel_customer_balance_hold(request: CancelHoldMoneyRequest) -> None`
  - `async CustomersCoreMixin.top_up_customer_balance(request: ChangeUserBalanceRequest) -> None` — ValueError, если `request.customer_id is None or request.wallet_id is None`
  - `async CustomersCoreMixin.withdraw_customer_balance(request: ChangeUserBalanceRequest) -> None` — та же валидация

- [ ] **Step 1: Failing tests**

В `tests/unit/test_customers.py` (импорты: `HoldMoneyRequest`, `HoldMoneyResponse`, `CancelHoldMoneyRequest`, `ChangeUserBalanceRequest`):

```python
async def test_hold_customer_balance_returns_transaction() -> None:
    """hold_customer_balance proxies HoldMoneyResponse."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_response = MagicMock(spec=HoldMoneyResponse)
    mock_api.hold_customer_balance = AsyncMock(return_value=mock_response)

    request = HoldMoneyRequest(
        customer_id=ORG_ID,
        organization_id=ORG_ID,
        wallet_id=ORG_ID,
        sum=100.0,
    )
    result = await manager.hold_customer_balance(request)

    assert result is mock_response
    mock_api.hold_customer_balance.assert_awaited_once_with(
        hold_money_request=request
    )


async def test_cancel_customer_balance_hold_calls_api() -> None:
    """cancel_customer_balance_hold delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.cancel_customer_balance_hold = AsyncMock(return_value={})

    request = CancelHoldMoneyRequest(
        organization_id=ORG_ID,
        transaction_id=ORG_ID,
    )
    result = await manager.cancel_customer_balance_hold(request)

    assert result is None
    mock_api.cancel_customer_balance_hold.assert_awaited_once_with(
        cancel_hold_money_request=request
    )


async def test_top_up_customer_balance_calls_api() -> None:
    """top_up_customer_balance delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.top_up_customer_balance = AsyncMock(return_value={})

    request = ChangeUserBalanceRequest(
        organization_id=ORG_ID,
        customer_id=ORG_ID,
        wallet_id=ORG_ID,
        sum=50.0,
    )
    result = await manager.top_up_customer_balance(request)

    assert result is None
    mock_api.top_up_customer_balance.assert_awaited_once_with(
        change_user_balance_request=request
    )


async def test_withdraw_customer_balance_calls_api() -> None:
    """withdraw_customer_balance delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.withdraw_customer_balance = AsyncMock(return_value={})

    request = ChangeUserBalanceRequest(
        organization_id=ORG_ID,
        customer_id=ORG_ID,
        wallet_id=ORG_ID,
        sum=50.0,
    )
    result = await manager.withdraw_customer_balance(request)

    assert result is None
    mock_api.withdraw_customer_balance.assert_awaited_once_with(
        change_user_balance_request=request
    )


@pytest.mark.parametrize("method_name", ["top_up_customer_balance", "withdraw_customer_balance"])
async def test_balance_change_requires_customer_and_wallet(method_name: str) -> None:
    """top_up/withdraw без customer_id или wallet_id -> ValueError, SDK не вызывается."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    for kwargs in (
        {"customer_id": None, "wallet_id": ORG_ID},
        {"customer_id": ORG_ID, "wallet_id": None},
    ):
        request = ChangeUserBalanceRequest(
            organization_id=ORG_ID, sum=10.0, **kwargs
        )
        with pytest.raises(ValueError, match="customer_id"):
            await getattr(manager, method_name)(request)
    mock_api.assert_not_called()
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Реализация**

Импорты в `core.py`: `HoldMoneyRequest`, `HoldMoneyResponse`, `CancelHoldMoneyRequest`, `ChangeUserBalanceRequest`.

```python
    @staticmethod
    def _require_balance_fields(request: ChangeUserBalanceRequest) -> None:
        """customerId/walletId в SDK optional, но семантически обязательны."""
        if request.customer_id is None or request.wallet_id is None:
            raise ValueError(
                "customer_id и wallet_id обязательны для операций с балансом"
            )

    async def hold_customer_balance(
        self,
        request: HoldMoneyRequest,
    ) -> HoldMoneyResponse:
        """Захолдировать средства на кошельке клиента.

        Идемпотентность — через request.transaction_id
        (если не задан, сервер сгенерирует и вернёт в ответе).
        """

        async def api_call() -> HoldMoneyResponse:
            api = await self.get_customers_api()
            return await api.hold_customer_balance(hold_money_request=request)

        return await self.execute_with_retry(
            ApiMethod.HOLD_CUSTOMER_BALANCE, api_call
        )

    async def cancel_customer_balance_hold(
        self,
        request: CancelHoldMoneyRequest,
    ) -> None:
        """Отменить холд по transactionId."""

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.cancel_customer_balance_hold(
                cancel_hold_money_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_CUSTOMER_BALANCE_HOLD, api_call
        )

    async def top_up_customer_balance(
        self,
        request: ChangeUserBalanceRequest,
    ) -> None:
        """Пополнить кошелёк клиента (sum строго положительная)."""

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.top_up_customer_balance(
                change_user_balance_request=request
            )

        self._require_balance_fields(request)
        return await self.execute_with_retry(
            ApiMethod.TOP_UP_CUSTOMER_BALANCE, api_call
        )

    async def withdraw_customer_balance(
        self,
        request: ChangeUserBalanceRequest,
    ) -> None:
        """Списать средства с кошелька клиента (sum строго положительная)."""

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.withdraw_customer_balance(
                change_user_balance_request=request
            )

        self._require_balance_fields(request)
        return await self.execute_with_retry(
            ApiMethod.WITHDRAW_CUSTOMER_BALANCE, api_call
        )
```

- [ ] **Step 4: Run — PASS**: `.venv/bin/python -m pytest tests/unit/test_customers.py -q`

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/customers/core.py tests/unit/test_customers.py
git commit -m "feat(customers): wallet balance hold/cancel/topup/withdraw wrappers"
```

---

### Task 4: Customers core — get_loyalty_counters

**Files:**
- Modify: `iikocloud/mixins/customers/core.py`
- Test: `tests/unit/test_customers.py`

**Interfaces:**
- Produces: `async CustomersCoreMixin.get_loyalty_counters(request: GetCountersRequest) -> GetCountersResponse`

- [ ] **Step 1: Failing test**

```python
async def test_get_loyalty_counters_returns_response() -> None:
    """get_loyalty_counters proxies GetCountersResponse."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_response = MagicMock(spec=GetCountersResponse)
    mock_api.get_loyalty_counters = AsyncMock(return_value=mock_response)

    request = GetCountersRequest(
        organization_id=ORG_ID,
        guest_ids=[ORG_ID],
        metrics=[CounterMetric.NUMBER_0],
        periods=[CounterPeriod.NUMBER_0],
    )
    result = await manager.get_loyalty_counters(request)

    assert result is mock_response
    mock_api.get_loyalty_counters.assert_awaited_once_with(
        get_counters_request=request
    )
```

(импорты: `GetCountersRequest`, `GetCountersResponse`, `CounterMetric`, `CounterPeriod`.)

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Реализация**

```python
    async def get_loyalty_counters(
        self,
        request: GetCountersRequest,
    ) -> GetCountersResponse:
        """Счётчики лояльности гостей (кол-во заказов/суммы за периоды).

        metrics/periods — числовые enum'ы SDK (CounterMetric 0..3,
        CounterPeriod 0..12); семантика значений — по документации iiko.
        """

        async def api_call() -> GetCountersResponse:
            api = await self.get_customers_api()
            return await api.get_loyalty_counters(get_counters_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_LOYALTY_COUNTERS, api_call
        )
```

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/customers/core.py tests/unit/test_customers.py
git commit -m "feat(customers): get_loyalty_counters wrapper"
```

---

### Task 5: Menu core — стоп-листы (add/remove/clear/check)

**Files:**
- Modify: `iikocloud/mixins/menu/core.py`
- Test: `tests/unit/test_menu.py`

**Interfaces:**
- Produces:
  - `async MenuCoreMixin.add_products_to_stop_list(request: AddProductsToStopListRequest) -> CorrelationIdResponse`
  - `async MenuCoreMixin.remove_products_from_stop_list(request: RemoveProductsFromStopListRequest) -> CorrelationIdResponse`
  - `async MenuCoreMixin.clear_stop_list(request: ClearStopListRequest) -> CorrelationIdResponse`
  - `async MenuCoreMixin.check_products_in_stop_list(request: CheckStopListRequest) -> CheckStopListResponse`

- [ ] **Step 1: Failing tests**

В `tests/unit/test_menu.py` (импорты: `AddProductsToStopListRequest`, `AddProductsToStopListItem`, `RemoveProductsFromStopListRequest`, `RemoveProductsFromStopListItem`, `ClearStopListRequest`, `CheckStopListRequest`, `CheckStopListResponse`, `CorrelationIdResponse`, `DeliveryOrderCreateProductItem`):

```python
async def test_add_products_to_stop_list_returns_correlation() -> None:
    """add_products_to_stop_list proxies CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.add_products_to_stop_list = AsyncMock(return_value=mock_response)

    request = AddProductsToStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
        items=[AddProductsToStopListItem(product_id=ORG_ID, balance=0.0)],
    )
    result = await manager.add_products_to_stop_list(request)

    assert result is mock_response
    mock_api.add_products_to_stop_list.assert_awaited_once_with(
        add_products_to_stop_list_request=request
    )


async def test_remove_products_from_stop_list_returns_correlation() -> None:
    """remove_products_from_stop_list proxies CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.remove_products_from_stop_list = AsyncMock(return_value=mock_response)

    request = RemoveProductsFromStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
        items=[RemoveProductsFromStopListItem(product_id=ORG_ID)],
    )
    result = await manager.remove_products_from_stop_list(request)

    assert result is mock_response
    mock_api.remove_products_from_stop_list.assert_awaited_once_with(
        remove_products_from_stop_list_request=request
    )


async def test_clear_stop_list_returns_correlation() -> None:
    """clear_stop_list proxies CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.clear_stop_list = AsyncMock(return_value=mock_response)

    request = ClearStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
    )
    result = await manager.clear_stop_list(request)

    assert result is mock_response
    mock_api.clear_stop_list.assert_awaited_once_with(
        clear_stop_list_request=request
    )


async def test_check_products_in_stop_list_returns_response() -> None:
    """check_products_in_stop_list proxies CheckStopListResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CheckStopListResponse)
    mock_api.check_products_in_stop_list = AsyncMock(return_value=mock_response)

    request = CheckStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
        items=[
            DeliveryOrderCreateProductItem(
                type="Product",
                product_id=ORG_ID,
                amount=1.0,
                price=1.0,
            )
        ],
    )
    result = await manager.check_products_in_stop_list(request)

    assert result is mock_response
    mock_api.check_products_in_stop_list.assert_awaited_once_with(
        check_stop_list_request=request
    )
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Реализация**

В `iikocloud/mixins/menu/core.py` импорты: `AddProductsToStopListRequest`, `RemoveProductsFromStopListRequest`, `ClearStopListRequest`, `CheckStopListRequest`, `CheckStopListResponse`, `CorrelationIdResponse`. Методы в `MenuCoreMixin`:

```python
    async def add_products_to_stop_list(
        self,
        request: AddProductsToStopListRequest,
    ) -> CorrelationIdResponse:
        """Добавить продукты в стоп-лист (async-операция, iiko >= 8.6.1).

        Returns:
            CorrelationIdResponse — статус применения через /api/1/commands/status
        """

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_menu_api()
            return await api.add_products_to_stop_list(
                add_products_to_stop_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_PRODUCTS_TO_STOP_LIST, api_call
        )

    async def remove_products_from_stop_list(
        self,
        request: RemoveProductsFromStopListRequest,
    ) -> CorrelationIdResponse:
        """Убрать продукты из стоп-листа (async-операция, iiko >= 8.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_menu_api()
            return await api.remove_products_from_stop_list(
                remove_products_from_stop_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.REMOVE_PRODUCTS_FROM_STOP_LIST, api_call
        )

    async def clear_stop_list(
        self,
        request: ClearStopListRequest,
    ) -> CorrelationIdResponse:
        """Очистить стоп-лист терминальной группы (async-операция)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_menu_api()
            return await api.clear_stop_list(clear_stop_list_request=request)

        return await self.execute_with_retry(ApiMethod.CLEAR_STOP_LIST, api_call)

    async def check_products_in_stop_list(
        self,
        request: CheckStopListRequest,
    ) -> CheckStopListResponse:
        """Проверить позиции заказа на наличие в стоп-листе.

        items — DeliveryOrderCreateProductItem (type="Product").
        rejectedItems == None означает «ничего не в стоп-листе».
        """

        async def api_call() -> CheckStopListResponse:
            api = await self.get_menu_api()
            return await api.check_products_in_stop_list(
                check_stop_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHECK_PRODUCTS_IN_STOP_LIST, api_call
        )
```

- [ ] **Step 4: Run — PASS**: `.venv/bin/python -m pytest tests/unit/test_menu.py -q`

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/menu/core.py tests/unit/test_menu.py
git commit -m "feat(menu): stop-list add/remove/clear/check wrappers"
```

---

### Task 6: Menu core — номенклатура и комбо

**Files:**
- Modify: `iikocloud/mixins/menu/core.py`
- Test: `tests/unit/test_menu.py`

**Interfaces:**
- Produces:
  - `async MenuCoreMixin.get_nomenclature(request: NomenclatureRequest) -> NomenclatureResponse`
  - `async MenuCoreMixin.get_combos_info(request: GetCombosInfoRequest) -> GetCombosInfoResponse`
  - `async MenuCoreMixin.calculate_combo_price(request: CalculateComboPriceRequest) -> CalculateComboPriceResponse`

- [ ] **Step 1: Failing tests**

```python
async def test_get_nomenclature_returns_response() -> None:
    """get_nomenclature proxies NomenclatureResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=NomenclatureResponse)
    mock_api.get_nomenclature = AsyncMock(return_value=mock_response)

    request = NomenclatureRequest(organization_id=ORG_ID, start_revision=0)
    result = await manager.get_nomenclature(request)

    assert result is mock_response
    mock_api.get_nomenclature.assert_awaited_once_with(
        nomenclature_request=request
    )


async def test_get_combos_info_returns_response() -> None:
    """get_combos_info proxies GetCombosInfoResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=GetCombosInfoResponse)
    mock_api.get_combos_info = AsyncMock(return_value=mock_response)

    request = GetCombosInfoRequest(organization_id=ORG_ID)
    result = await manager.get_combos_info(request)

    assert result is mock_response
    mock_api.get_combos_info.assert_awaited_once_with(
        get_combos_info_request=request
    )


async def test_calculate_combo_price_returns_response() -> None:
    """calculate_combo_price proxies CalculateComboPriceResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CalculateComboPriceResponse)
    mock_api.calculate_combo_price = AsyncMock(return_value=mock_response)

    request = CalculateComboPriceRequest(
        organization_id=ORG_ID,
        items=[
            DeliveryOrderCreateProductItem(
                type="Product",
                product_id=ORG_ID,
                amount=1.0,
                price=1.0,
            )
        ],
    )
    result = await manager.calculate_combo_price(request)

    assert result is mock_response
    mock_api.calculate_combo_price.assert_awaited_once_with(
        calculate_combo_price_request=request
    )
```

(импорты: `NomenclatureRequest`, `NomenclatureResponse`, `GetCombosInfoRequest`, `GetCombosInfoResponse`, `CalculateComboPriceRequest`, `CalculateComboPriceResponse`.)

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Реализация**

```python
    async def get_nomenclature(
        self,
        request: NomenclatureRequest,
    ) -> NomenclatureResponse:
        """Номенклатура организации (группы, продукты, размеры).

        Дельта-синхронизация: start_revision=0 — полная выгрузка;
        далее — revision из предыдущего ответа. Если revision ответа
        == start_revision, меню не менялось (списки пустые).
        Лимит iiko: не более 5 организаций за раз от одного API-логина,
        не чаще раза в минуту.
        """

        async def api_call() -> NomenclatureResponse:
            api = await self.get_menu_api()
            return await api.get_nomenclature(nomenclature_request=request)

        return await self.execute_with_retry(ApiMethod.GET_NOMENCLATURE, api_call)

    async def get_combos_info(
        self,
        request: GetCombosInfoRequest,
    ) -> GetCombosInfoResponse:
        """Все комбо организации (категории и спецификации)."""

        async def api_call() -> GetCombosInfoResponse:
            api = await self.get_menu_api()
            return await api.get_combos_info(get_combos_info_request=request)

        return await self.execute_with_retry(ApiMethod.GET_COMBOS_INFO, api_call)

    async def calculate_combo_price(
        self,
        request: CalculateComboPriceRequest,
    ) -> CalculateComboPriceResponse:
        """Расчёт цены комбо по позициям.

        Если incorrectlyFilledGroups не пуст — price будет 0.
        """

        async def api_call() -> CalculateComboPriceResponse:
            api = await self.get_menu_api()
            return await api.calculate_combo_price(
                calculate_combo_price_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CALCULATE_COMBO_PRICE, api_call
        )
```

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/menu/core.py tests/unit/test_menu.py
git commit -m "feat(menu): nomenclature and combos wrappers"
```

---

### Task 7: Integration read-тесты + маркер danger_write

**Files:**
- Modify: `pyproject.toml` (markers), `tests/integration/conftest.py:78-83` (`_section_for`)
- Create: `tests/integration/menu/test_nomenclature_combos.py`
- Create: `tests/integration/customers/test_loyalty_read.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id` из `tests/integration/conftest.py`
- Produces: маркер `danger_write` (роутинг на write-секцию)

- [ ] **Step 1: Маркер и роутинг**

В `pyproject.toml` в `markers` добавить:

```toml
    "danger_write: Write tests that create/cancel orders, mutate stop lists or balances on the dedicated write organization",
```

В `tests/integration/conftest.py` `_section_for`:

```python
def _section_for(request: pytest.FixtureRequest) -> str:
    """Выбрать сервер по маркеру теста: write/test_server/danger_write → write, иначе read."""
    node = request.node
    if (
        node.get_closest_marker("write")
        or node.get_closest_marker("test_server")
        or node.get_closest_marker("danger_write")
    ):
        return WRITE
    return READ
```

- [ ] **Step 2: Тесты меню**

`tests/integration/menu/test_nomenclature_combos.py`:

```python
"""Интеграционные read-тесты Menu API: номенклатура и комбо.

Запуск:
    uv run pytest tests/integration/menu/test_nomenclature_combos.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    GetCombosInfoRequest,
    NomenclatureRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestGetNomenclature:
    """get_nomenclature против реального API."""

    async def test_full_nomenclature_returns_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Полная выгрузка (start_revision=0): revision + списки."""
        response = await manager.get_nomenclature(
            NomenclatureRequest(organization_id=organization_id, start_revision=0)
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert isinstance(response.revision, int)
        assert response.groups is not None
        assert response.products is not None
        assert response.sizes is not None

    async def test_same_revision_returns_empty_delta(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Повтор с revision из прошлого ответа -> списки пустые."""
        first = await manager.get_nomenclature(
            NomenclatureRequest(organization_id=organization_id, start_revision=0)
        )
        second = await manager.get_nomenclature(
            NomenclatureRequest(
                organization_id=organization_id,
                start_revision=first.revision,
            )
        )

        assert second.revision == first.revision
        assert second.products == [] or second.products is None


class TestGetCombosInfo:
    """get_combos_info против реального API."""

    async def test_get_combos_info_returns_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Ответ содержит категории/спецификации комбо (могут быть пустыми)."""
        response = await manager.get_combos_info(
            GetCombosInfoRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.combo_categories is not None
        assert response.combo_specifications is not None
```

- [ ] **Step 3: Тест customers counters**

`tests/integration/customers/test_loyalty_read.py`:

```python
"""Интеграционные read-тесты лояльности Customers API.

Запуск:
    uv run pytest tests/integration/customers/test_loyalty_read.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    CounterMetric,
    CounterPeriod,
    GetCountersRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestGetLoyaltyCounters:
    """get_loyalty_counters против реального API."""

    async def test_counters_for_unknown_guest_returns_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Запрос по несуществующему guest -> валидный ответ со списком counters."""
        response = await manager.get_loyalty_counters(
            GetCountersRequest(
                organization_id=organization_id,
                guest_ids=[UUID("00000000-0000-0000-0000-000000000001")],
                metrics=[CounterMetric.NUMBER_0],
                periods=[CounterPeriod.NUMBER_0],
            )
        )

        assert response is not None
        assert response.counters is not None
```

- [ ] **Step 4: Прогон read integration**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/menu/test_nomenclature_combos.py tests/integration/customers/test_loyalty_read.py -q`
Expected: PASS (или skip с явной причиной, если стенд не поддерживает — тогда зафиксировать причину в docstring теста).

Если `test_same_revision_returns_empty_delta` падает из-за поведения стенда (revision всегда растёт), ослабить до `assert second.revision >= first.revision` с комментарием.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/integration/conftest.py tests/integration/menu/test_nomenclature_combos.py tests/integration/customers/test_loyalty_read.py
git commit -m "test: integration read for nomenclature, combos, loyalty counters; danger_write marker"
```

---

### Task 8: Integration danger_write-тесты (карты, программа, баланс, стоп-листы)

**Files:**
- Create: `tests/integration/customers/test_loyalty_write.py`
- Create: `tests/integration/menu/test_stop_lists_write.py`

**Interfaces:**
- Consumes: `manager`, `organization_id`; `generate_random_phone` из `tests/conftest.py`; `_is_crm_unavailable`-паттерн из `tests/integration/customers/test_lifecycle.py`
- Produces: —

- [ ] **Step 1: Тесты лояльности write**

`tests/integration/customers/test_loyalty_write.py`:

```python
"""Интеграционные danger_write-тесты лояльности (write-секция).

Карты: add -> remove. Баланс: hold -> cancel_hold и top_up -> withdraw.
Требуют write-стенд с Loyalty/CRM и кошельком у тестового клиента;
при отсутствии — skip с явной причиной.

Запуск:
    uv run pytest tests/integration/customers/test_loyalty_write.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID, uuid4

import pytest
from iikocloud_client import (
    AddMagnetCardRequest,
    CancelHoldMoneyRequest,
    ChangeUserBalanceRequest,
    CreateOrUpdateCustomerRequest,
    DeleteCustomersRequest,
    DeleteMagnetCardRequest,
    GetCustomerInfoRequest,
    HoldMoneyRequest,
)
from iikocloud_client.exceptions import ApiException

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


def _is_crm_unavailable(exc: BaseException) -> bool:
    body = getattr(exc, "body", None) or str(exc)
    return (
        "Transport_WrongCrmId" in body
        or "Common_OrganizationNotFound" in body
        or "Organization not found" in body
    )


def _is_loyalty_unavailable(exc: BaseException) -> bool:
    """Стенд без программ лояльности/кошельков."""
    body = getattr(exc, "body", None) or str(exc)
    return "Loyalty" in body or "wallet" in body.lower() or "program" in body.lower()


@pytest.fixture
async def test_customer(
    manager: IikoCloudApiClientManager, organization_id: UUID
):
    """Тестовый клиент на write-стенде; удаляется после теста."""
    customer_id: UUID | None = None
    try:
        response = await manager.create_or_update_customer(
            CreateOrUpdateCustomerRequest(
                organization_id=organization_id,
                phone=generate_random_phone(),
                name="Loyalty Write Test",
            )
        )
        customer_id = response.id
        yield customer_id
    except ApiException as exc:
        if _is_crm_unavailable(exc):
            pytest.skip("Write-стенд без CRM/Loyalty")
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


class TestMagnetCards:
    async def test_add_and_remove_magnet_card(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
    ) -> None:
        card_number = f"9{uuid4().int % 10**15:015d}"
        card_track = f"track-{uuid4().hex[:12]}"
        try:
            await manager.add_customer_magnet_card(
                AddMagnetCardRequest(
                    card_number=card_number,
                    card_track=card_track,
                    customer_id=test_customer,
                    organization_id=organization_id,
                )
            )
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.remove_customer_magnet_card(
                DeleteMagnetCardRequest(
                    card_track=card_track,
                    customer_id=test_customer,
                    organization_id=organization_id,
                )
            )
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд не поддерживает карты: {exc}")
            raise


class TestBalance:
    async def _wallet_id(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        customer_id: UUID,
    ) -> UUID:
        """Первый кошелёк клиента из get_customer_info (wallet_balances)."""
        info = await manager.get_customer_info(
            GetCustomerInfoRequest(
                organization_id=organization_id, id=customer_id
            )
        )
        balances = info.wallet_balances or []
        if not balances or balances[0].id is None:
            pytest.skip("У тестового клиента нет кошелька лояльности")
        return balances[0].id

    async def test_hold_and_cancel_balance(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
    ) -> None:
        wallet_id = await self._wallet_id(manager, organization_id, test_customer)
        try:
            hold = await manager.hold_customer_balance(
                HoldMoneyRequest(
                    customer_id=test_customer,
                    organization_id=organization_id,
                    wallet_id=wallet_id,
                    sum=1.0,
                    comment="integration test",
                    transaction_id=uuid4(),
                )
            )
            assert hold is not None
            transaction_id = hold.transaction_id
            assert transaction_id is not None
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.cancel_customer_balance_hold(
                CancelHoldMoneyRequest(
                    organization_id=organization_id,
                    transaction_id=transaction_id,
                )
            )
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд не поддерживает баланс: {exc}")
            raise

    async def test_top_up_and_withdraw_balance(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
    ) -> None:
        wallet_id = await self._wallet_id(manager, organization_id, test_customer)
        amount = 1.0
        try:
            await manager.top_up_customer_balance(
                ChangeUserBalanceRequest(
                    organization_id=organization_id,
                    customer_id=test_customer,
                    wallet_id=wallet_id,
                    sum=amount,
                    comment="integration test topup",
                )
            )
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.withdraw_customer_balance(
                ChangeUserBalanceRequest(
                    organization_id=organization_id,
                    customer_id=test_customer,
                    wallet_id=wallet_id,
                    sum=amount,
                    comment="integration test withdraw",
                )
            )
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд не поддерживает баланс: {exc}")
            raise
```

(Поле кошельков сверено с SDK: `GetCustomerInfoResponse.wallet_balances`
→ `List[GuestBalanceInfo]`, у элемента — `.id`.)

- [ ] **Step 2: Тесты стоп-листов write**

`tests/integration/menu/test_stop_lists_write.py`:

```python
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
from uuid import UUID

import pytest
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


@pytest.fixture
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


@pytest.fixture
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
                import logging

                logging.getLogger(__name__).warning("clear_stop_list cleanup: %s", exc)
```

- [ ] **Step 3: Тест add_customer_to_program (в `test_loyalty_write.py`)**

Добавить класс (импорт `AddCustomerToProgramRequest` пополнить):

```python
class TestAddCustomerToProgram:
    async def test_add_customer_to_default_program(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
    ) -> None:
        """Добавление в программу по умолчанию (program_id не задан).

        programId в модели optional — сервер привязывает к программе
        по умолчанию. Если на стенде нет программ лояльности — skip.
        """
        try:
            response = await manager.add_customer_to_program(
                AddCustomerToProgramRequest(
                    customer_id=test_customer,
                    organization_id=organization_id,
                )
            )
            assert response is not None
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд без программ лояльности: {exc}")
            raise
```

- [ ] **Step 4: Прогон danger_write**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/customers/test_loyalty_write.py tests/integration/menu/test_stop_lists_write.py -q`
Expected: PASS или skip с явной причиной (стенд без CRM/кошелька/прав). Skip-причины зафиксировать в отчёте пользователю — это открытая точка спеки (наличие программы лояльности на write-организации).

- [ ] **Step 5: Полный регрессионный прогон**

Run: `.venv/bin/python -m pytest tests/unit -q && IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration -q`
Expected: unit — все PASS; integration — все PASS/skip.

- [ ] **Step 6: Commit**

```bash
git add tests/integration/customers/test_loyalty_write.py tests/integration/menu/test_stop_lists_write.py
git commit -m "test: danger_write loyalty balance/cards/program and stop-list lifecycle against write org"
```
