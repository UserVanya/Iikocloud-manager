# DiscountsAndPromotions Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обёртки над 6 методами `DiscountsAndPromotionsApi` + helper `calculate_order_loyalty` + unit- и integration-тесты.

**Architecture:** Новый домен `iikocloud/mixins/discounts/` (`core.py` + `helpers.py`), регистрация через `DiscountsHelpersMixin` в MRO.

**Spec:** `docs/superpowers/specs/2026-07-25-discounts-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- `ApiMethod` value == snake_case имени метода SDK (Locked Names).
- Rate limits: `calculate_loyalty_checkin` — **1000/60s**; `get_coupon_info`, `get_non_activated_coupons_by_series` — 10/60s; `get_coupon_series`, `get_loyalty_manual_conditions`, `get_loyalty_programs` — 1/60s.
- SDK kwargs: `calculate_checkin_request`, `coupon_info_request`, `series_with_not_activated_coupons_request`, `get_by_organization_id_request`, `get_programs_request`, `not_activated_coupon_request`.
- `get_loyalty_manual_conditions`: `organization_id` в модели optional — обёртка валидирует (ValueError до вызова SDK).
- Проверки качества: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура

**Files:**
- Modify: `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: 6 `ApiMethod`; `async _ManagerBase.get_discounts_and_promotions_api() -> DiscountsAndPromotionsApi`

Locked names: `calculate_loyalty_checkin`, `get_coupon_info`, `get_coupon_series`, `get_loyalty_manual_conditions`, `get_loyalty_programs`, `get_non_activated_coupons_by_series`.

- [ ] **Step 1: Failing test**

```python
def test_discounts_methods_have_limits() -> None:
    """6 методов discounts есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "calculate_loyalty_checkin": 1000 / 60.0,
        "get_coupon_info": 10 / 60.0,
        "get_coupon_series": 1 / 60.0,
        "get_loyalty_manual_conditions": 1 / 60.0,
        "get_loyalty_programs": 1 / 60.0,
        "get_non_activated_coupons_by_series": 10 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация**

В `_base.py`: импорт `DiscountsAndPromotionsApi` (алфавитно); `ApiMethod` секция `# Discounts & Promotions` с 6 значениями (`CALCULATE_LOYALTY_CHECKIN = "calculate_loyalty_checkin"` и т.д.); 6 полей в `MethodRateLimits`; слот `_discounts_and_promotions_api: DiscountsAndPromotionsApi | None` + геттер. В `api_client_manager.py.__init__`: слот + импорт. В `config_reader.py` (комментарий `# Discounts & Promotions`): 6 полей по таблице. В `config.example.yml`: 6 блоков.

- [ ] **Step 4: Run — PASS + качество**: unit +1, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/api_client_manager.py iikocloud/config_reader.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limits and lazy client for discounts and promotions"
```

---

### Task 2: Core + helper + регистрация

**Files:**
- Create: `iikocloud/mixins/discounts/{__init__,core,helpers}.py`
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO + docstring)
- Test: `tests/unit/test_discounts.py`

**Interfaces:**
- Produces: `DiscountsCoreMixin` (6 методов); `DiscountsHelpersMixin(DiscountsCoreMixin)`:
  - `async calculate_order_loyalty(organization_id: str | UUID, items: list[DeliveryOrderCreateItem], phone: str, *, coupon: str | None = None, customer: DeliveryOrderCreateCustomer | None = None, applicable_manual_conditions: list[UUID] | None = None, order_service_type: str | None = None, terminal_group_id: str | UUID | None = None) -> CalculateCheckinResponse`

Минимальные модели (проверены; `u = ORG_ID`):

```python
item = DeliveryOrderCreateProductItem(type="Product", product_id=u, amount=1.0, price=1.0)
payload = DeliveryOrderCreatePayload(phone="+79990001122", items=[item])
CalculateCheckinRequest(organization_id=u, order=payload)
CouponInfoRequest(number="123", organization_id=u)
SeriesWithNotActivatedCouponsRequest(organization_id=u)
GetByOrganizationIdRequest(organization_id=u)
GetProgramsRequest(organization_id=u)
NotActivatedCouponRequest(organization_id=u, series="S")
```

- [ ] **Step 1: Failing tests**

`tests/unit/test_discounts.py`:

```python
"""Unit tests for Discounts domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CalculateCheckinRequest,
    CalculateCheckinResponse,
    CouponInfoRequest,
    CouponInfoResponse,
    DeliveryOrderCreatePayload,
    DeliveryOrderCreateProductItem,
    GetByOrganizationIdRequest,
    GetManualConditionsResponse,
    GetProgramsRequest,
    GetProgramsResponse,
    NotActivatedCouponRequest,
    NotActivatedCouponResponse,
    SeriesWithNotActivatedCouponsRequest,
    SeriesWithNotActivatedCouponsResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_discounts_and_promotions_api"

METHODS: list[tuple[str, object, str, type]] = [
    (
        "calculate_loyalty_checkin",
        CalculateCheckinRequest(
            organization_id=ORG_ID,
            order=DeliveryOrderCreatePayload(
                phone="+79990001122",
                items=[
                    DeliveryOrderCreateProductItem(
                        type="Product", product_id=ORG_ID, amount=1.0, price=1.0
                    )
                ],
            ),
        ),
        "calculate_checkin_request",
        CalculateCheckinResponse,
    ),
    (
        "get_coupon_info",
        CouponInfoRequest(number="123", organization_id=ORG_ID),
        "coupon_info_request",
        CouponInfoResponse,
    ),
    (
        "get_coupon_series",
        SeriesWithNotActivatedCouponsRequest(organization_id=ORG_ID),
        "series_with_not_activated_coupons_request",
        SeriesWithNotActivatedCouponsResponse,
    ),
    (
        "get_loyalty_manual_conditions",
        GetByOrganizationIdRequest(organization_id=ORG_ID),
        "get_by_organization_id_request",
        GetManualConditionsResponse,
    ),
    (
        "get_loyalty_programs",
        GetProgramsRequest(organization_id=ORG_ID),
        "get_programs_request",
        GetProgramsResponse,
    ),
    (
        "get_non_activated_coupons_by_series",
        NotActivatedCouponRequest(organization_id=ORG_ID, series="S"),
        "not_activated_coupon_request",
        NotActivatedCouponResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_discounts_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 6 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


async def test_manual_conditions_requires_organization_id() -> None:
    """organization_id=None -> ValueError, SDK не вызывается."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)

    request = GetByOrganizationIdRequest(organization_id=None)
    with pytest.raises(ValueError, match="organization_id"):
        await manager.get_loyalty_manual_conditions(request)
    mock_api.get_loyalty_manual_conditions.assert_not_called()


async def test_calculate_order_loyalty_builds_payload() -> None:
    """Helper собирает DeliveryOrderCreatePayload с loyalty_info."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CalculateCheckinResponse)
    mock_api.calculate_loyalty_checkin = AsyncMock(return_value=mock_response)

    item = manager.build_product_item(product_id=ORG_ID, price=150.0)
    result = await manager.calculate_order_loyalty(
        organization_id=str(ORG_ID),
        items=[item],
        phone="+79990001122",
        coupon="COUPON1",
        order_service_type="DeliveryByClient",
    )

    assert result is mock_response
    call_kwargs = mock_api.calculate_loyalty_checkin.await_args.kwargs
    request = call_kwargs["calculate_checkin_request"]
    assert isinstance(request, CalculateCheckinRequest)
    assert request.organization_id == ORG_ID
    order = request.order
    assert order.phone == "+79990001122"
    assert order.items == [item]
    assert order.loyalty_info is not None
    assert order.loyalty_info.coupon == "COUPON1"
    assert order.order_service_type is not None
```

Примечание: реальный `DeliveryOrderCreatePayload` в таблице обязателен — pydantic не примет MagicMock/заглушку на месте вложенной модели (проверено: минимальная конструкция работает).

- [ ] **Step 2: Run — FAIL** (AttributeError)

- [ ] **Step 3: Реализация**

`__init__.py` — реэкспорты по конвенции. `core.py`:

```python
"""Discounts core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CalculateCheckinRequest,
    CalculateCheckinResponse,
    CouponInfoRequest,
    CouponInfoResponse,
    GetByOrganizationIdRequest,
    GetManualConditionsResponse,
    GetProgramsRequest,
    GetProgramsResponse,
    NotActivatedCouponRequest,
    NotActivatedCouponResponse,
    SeriesWithNotActivatedCouponsRequest,
    SeriesWithNotActivatedCouponsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DiscountsCoreMixin(_ManagerBase):
    """Core-методы DiscountsAndPromotions API (все read-only)."""

    async def calculate_loyalty_checkin(
        self,
        request: CalculateCheckinRequest,
    ) -> CalculateCheckinResponse:
        """Расчёт скидок/лояльности для заказа (высокочастотный вызов).

        Верхнеуровневые coupon/manual_conditions/dynamic_discounts в
        request — obsolete; передавать через order.loyalty_info.
        """

        async def api_call() -> CalculateCheckinResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.calculate_loyalty_checkin(
                calculate_checkin_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CALCULATE_LOYALTY_CHECKIN, api_call
        )

    async def get_coupon_info(
        self,
        request: CouponInfoRequest,
    ) -> CouponInfoResponse:
        """Информация о купоне по номеру."""

        async def api_call() -> CouponInfoResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_coupon_info(coupon_info_request=request)

        return await self.execute_with_retry(ApiMethod.GET_COUPON_INFO, api_call)

    async def get_coupon_series(
        self,
        request: SeriesWithNotActivatedCouponsRequest,
    ) -> SeriesWithNotActivatedCouponsResponse:
        """Серии купонов с неудалёнными неактивированными купонами."""

        async def api_call() -> SeriesWithNotActivatedCouponsResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_coupon_series(
                series_with_not_activated_coupons_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_COUPON_SERIES, api_call
        )

    async def get_loyalty_manual_conditions(
        self,
        request: GetByOrganizationIdRequest,
    ) -> GetManualConditionsResponse:
        """Все ручные условия организации.

        Raises:
            ValueError: organization_id не задан (в модели optional)
        """
        if request.organization_id is None:
            raise ValueError("organization_id обязателен")

        async def api_call() -> GetManualConditionsResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_loyalty_manual_conditions(
                get_by_organization_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_LOYALTY_MANUAL_CONDITIONS, api_call
        )

    async def get_loyalty_programs(
        self,
        request: GetProgramsRequest,
    ) -> GetProgramsResponse:
        """Все программы лояльности организации."""

        async def api_call() -> GetProgramsResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_loyalty_programs(get_programs_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_LOYALTY_PROGRAMS, api_call
        )

    async def get_non_activated_coupons_by_series(
        self,
        request: NotActivatedCouponRequest,
    ) -> NotActivatedCouponResponse:
        """Неактивированные купоны серии (page/page_size-пагинация)."""

        async def api_call() -> NotActivatedCouponResponse:
            api = await self.get_discounts_and_promotions_api()
            return await api.get_non_activated_coupons_by_series(
                not_activated_coupon_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_NON_ACTIVATED_COUPONS_BY_SERIES, api_call
        )
```

`helpers.py`:

```python
"""Discounts helpers mixin — convenience-методы расчёта лояльности."""

from uuid import UUID

from iikocloud_client import (
    CalculateCheckinRequest,
    CalculateCheckinResponse,
    DeliveryOrderCreateCustomer,
    DeliveryOrderCreateItem,
    DeliveryOrderCreateLoyaltyInfo,
    DeliveryOrderCreatePayload,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.discounts.core import DiscountsCoreMixin


class DiscountsHelpersMixin(DiscountsCoreMixin):
    """Публичный discounts mixin с convenience-методами."""

    async def calculate_order_loyalty(
        self,
        organization_id: str | UUID,
        items: list[DeliveryOrderCreateItem],
        phone: str,
        *,
        coupon: str | None = None,
        customer: DeliveryOrderCreateCustomer | None = None,
        applicable_manual_conditions: list[UUID] | None = None,
        order_service_type: str | None = None,
        terminal_group_id: str | UUID | None = None,
    ) -> CalculateCheckinResponse:
        """Расчёт скидок/лояльности заказа (короткая форма calculate).

        items собираются через build_product_item / build_compound_item.
        Купон и ручные условия передаются через order.loyalty_info
        (верхнеуровневые поля request — obsolete).
        """
        loyalty_info = None
        if coupon is not None or applicable_manual_conditions is not None:
            loyalty_info = DeliveryOrderCreateLoyaltyInfo(
                coupon=coupon,
                applicable_manual_conditions=applicable_manual_conditions,
            )
        order = DeliveryOrderCreatePayload(
            phone=phone,
            items=items,
            loyalty_info=loyalty_info,
            customer=customer,
            order_service_type=order_service_type,
        )
        return await self.calculate_loyalty_checkin(
            CalculateCheckinRequest(
                organization_id=as_uuid(organization_id),
                order=order,
                terminal_group_id=(
                    as_uuid(terminal_group_id) if terminal_group_id else None
                ),
            )
        )
```

Проверить при реализации: `DeliveryOrderCreatePayload.order_service_type` — тип `DeliveryOrderCreateServiceType` (str-enum) или str; если enum — передавать `DeliveryOrderCreateServiceType(order_service_type)` или принимать enum в сигнатуре (выбрать по факту модели).

В `api_client_manager.py`: импорт `DiscountsHelpersMixin`, MRO, docstring (`discounts`).

- [ ] **Step 4: Run — PASS + качество**: unit +8, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/discounts iikocloud/api_client_manager.py tests/unit/test_discounts.py
git commit -m "feat(discounts): 6 loyalty wrappers and calculate_order_loyalty helper"
```

---

### Task 3: Integration structure-only (test_server)

**Files:**
- Create: `tests/integration/customers/test_discounts_read.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`, `product` (root integration conftest)

- [ ] **Step 1: Тест**

`tests/integration/customers/test_discounts_read.py`:

```python
"""Structure-only read-тесты DiscountsAndPromotions (write-секция через test_server).

Запуск:
    uv run pytest tests/integration/customers/test_discounts_read.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    GetByOrganizationIdRequest,
    GetProgramsRequest,
    NotActivatedCouponRequest,
    SeriesWithNotActivatedCouponsRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestDiscountsRead:
    async def test_get_loyalty_programs_finds_bonus_program(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """На write-стенде есть программа лояльности («Бонусы»)."""
        response = await manager.get_loyalty_programs(
            GetProgramsRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.programs is not None
        assert len(response.programs) > 0
        program = response.programs[0]
        assert program.id is not None
        assert isinstance(program.name, str)

    async def test_get_loyalty_manual_conditions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_loyalty_manual_conditions(
            GetByOrganizationIdRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.manual_conditions is not None

    async def test_get_coupon_series_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_coupon_series(
            SeriesWithNotActivatedCouponsRequest(
                organization_id=organization_id
            )
        )

        assert response is not None
        assert response.series_with_not_activated_coupons is not None

    async def test_coupon_info_from_series(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """coupon_info по первому купону первой серии (skip, если купонов нет)."""
        series_response = await manager.get_coupon_series(
            SeriesWithNotActivatedCouponsRequest(
                organization_id=organization_id
            )
        )
        series = series_response.series_with_not_activated_coupons or []
        if not series:
            pytest.skip("Нет серий купонов на write-стенде")

        coupons = await manager.get_non_activated_coupons_by_series(
            NotActivatedCouponRequest(
                organization_id=organization_id,
                series=series[0].number,
                page_size=1,
            )
        )
        coupon_list = coupons.not_activated_coupon or []
        if not coupon_list:
            pytest.skip("Нет неактивированных купонов в серии")

        from iikocloud_client import CouponInfoRequest

        info = await manager.get_coupon_info(
            CouponInfoRequest(
                number=coupon_list[0].number, organization_id=organization_id
            )
        )
        assert info is not None
        assert info.coupon_info is not None

    async def test_calculate_order_loyalty_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        """Расчёт лояльности по минимальному заказу (helper)."""
        from tests.conftest import generate_random_phone

        product_id, price = product
        item = manager.build_product_item(product_id=product_id, price=price)

        response = await manager.calculate_order_loyalty(
            organization_id=organization_id,
            items=[item],
            phone=generate_random_phone(),
            order_service_type="DeliveryByClient",
        )

        assert response is not None
        # Расчёт всегда возвращает структуру, даже без применимых программ
        assert response.loyalty_program_results is not None or (
            response.warnings is not None
        )
```

- [ ] **Step 2: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/customers/test_discounts_read.py -q -rs`
Expected: PASS или skip с явной причиной.

- [ ] **Step 3: Регрессия + качество**: unit suite, ruff/mypy чисто
- [ ] **Step 4: Commit**

```bash
git add tests/integration/customers/test_discounts_read.py
git commit -m "test: discounts and promotions structure-only integration tests"
```
