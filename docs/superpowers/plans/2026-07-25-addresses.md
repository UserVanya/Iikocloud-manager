# Addresses Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обёртки над 4 методами `AddressesApi` + unit- и read integration-тесты.

**Architecture:** Новый домен `iikocloud/mixins/addresses/` (`core.py` + `helpers.py`-заготовка), регистрация через `AddressesHelpersMixin` в MRO.

**Spec:** `docs/superpowers/specs/2026-07-25-addresses-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- `ApiMethod` value == snake_case имени метода SDK (Locked Names).
- Rate limits: все 4 метода — 1/60s (справочники).
- SDK kwargs: `cities_request`, `regions_request`, `streets_by_city_request`, `streets_by_id_request`.
- Проверки качества после каждой задачи: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура (ApiMethod, лимиты, lazy-клиент)

**Files:**
- Modify: `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: `ApiMethod.GET_CITIES`, `GET_REGIONS`, `GET_STREETS_BY_CITY`, `GET_STREETS_BY_ID`; `async _ManagerBase.get_addresses_api() -> AddressesApi`

- [ ] **Step 1: Failing test**

В `tests/unit/test_config_reader.py`:

```python
def test_addresses_methods_have_limits() -> None:
    """4 метода addresses есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    names = ["get_cities", "get_regions", "get_streets_by_city", "get_streets_by_id"]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            1 / 60.0
        )
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Реализация**

В `iikocloud/mixins/_base.py`:
1. Импорт `AddressesApi` (алфавитно, первым среди API-классов).
2. В `ApiMethod`:

```python
    # Addresses
    GET_CITIES = "get_cities"
    GET_REGIONS = "get_regions"
    GET_STREETS_BY_CITY = "get_streets_by_city"
    GET_STREETS_BY_ID = "get_streets_by_id"
```

3. В `MethodRateLimits` — 4 поля `RateLimitConfig`.
4. Слот `_addresses_api: AddressesApi | None` + геттер `get_addresses_api()` (паттерн соседних).

В `iikocloud/api_client_manager.py.__init__`: `self._addresses_api = None` + импорт.

В `iikocloud/config_reader.py` (комментарий `# Addresses`):

```python
    get_cities: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_regions: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_streets_by_city: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_streets_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
```

В `config.example.yml` — 4 блока (1/60.0).

- [ ] **Step 4: Run — PASS + качество**: unit +1 passed, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/api_client_manager.py iikocloud/config_reader.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limits and lazy client for addresses"
```

---

### Task 2: Core + helpers-заготовка + регистрация

**Files:**
- Create: `iikocloud/mixins/addresses/{__init__,core,helpers}.py`
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO + docstring)
- Test: `tests/unit/test_addresses.py`

**Interfaces:**
- Produces: `AddressesCoreMixin` с 4 методами; `AddressesHelpersMixin(AddressesCoreMixin)` — заготовка

Минимальные модели (проверены; `u = ORG_ID`):

```python
CitiesRequest(organization_ids=[u])
RegionsRequest(organization_ids=[u])
StreetsByCityRequest(organization_id=u, city_id=u)
StreetsByIdRequest(organization_id=u, ids=[u])
```

- [ ] **Step 1: Failing tests**

`tests/unit/test_addresses.py`:

```python
"""Unit tests for Addresses domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CitiesRequest,
    CitiesResponse,
    RegionsRequest,
    RegionsResponse,
    StreetsByCityRequest,
    StreetsByIdRequest,
    StreetsByIdResponse,
    StreetsResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_addresses_api"

METHODS = [
    (
        "get_cities",
        CitiesRequest(organization_ids=[ORG_ID]),
        "cities_request",
        CitiesResponse,
    ),
    (
        "get_regions",
        RegionsRequest(organization_ids=[ORG_ID]),
        "regions_request",
        RegionsResponse,
    ),
    (
        "get_streets_by_city",
        StreetsByCityRequest(organization_id=ORG_ID, city_id=ORG_ID),
        "streets_by_city_request",
        StreetsResponse,
    ),
    (
        "get_streets_by_id",
        StreetsByIdRequest(organization_id=ORG_ID, ids=[ORG_ID]),
        "streets_by_id_request",
        StreetsByIdResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_addresses_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 4 метода проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
```

- [ ] **Step 2: Run — FAIL** (AttributeError)

- [ ] **Step 3: Реализация**

`iikocloud/mixins/addresses/__init__.py`:

```python
"""Addresses domain mixins."""

from iikocloud.mixins.addresses.core import AddressesCoreMixin
from iikocloud.mixins.addresses.helpers import AddressesHelpersMixin

__all__ = ["AddressesCoreMixin", "AddressesHelpersMixin"]
```

`iikocloud/mixins/addresses/core.py`:

```python
"""Addresses core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CitiesRequest,
    CitiesResponse,
    RegionsRequest,
    RegionsResponse,
    StreetsByCityRequest,
    StreetsByIdRequest,
    StreetsByIdResponse,
    StreetsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class AddressesCoreMixin(_ManagerBase):
    """Core-методы Addresses API (гео-справочники, read-only)."""

    async def get_cities(self, request: CitiesRequest) -> CitiesResponse:
        """Города организаций (ответ сгруппирован per-organization)."""

        async def api_call() -> CitiesResponse:
            api = await self.get_addresses_api()
            return await api.get_cities(cities_request=request)

        return await self.execute_with_retry(ApiMethod.GET_CITIES, api_call)

    async def get_regions(self, request: RegionsRequest) -> RegionsResponse:
        """Регионы (районы) организаций."""

        async def api_call() -> RegionsResponse:
            api = await self.get_addresses_api()
            return await api.get_regions(regions_request=request)

        return await self.execute_with_retry(ApiMethod.GET_REGIONS, api_call)

    async def get_streets_by_city(
        self, request: StreetsByCityRequest
    ) -> StreetsResponse:
        """Улицы города (одиночная organization_id)."""

        async def api_call() -> StreetsResponse:
            api = await self.get_addresses_api()
            return await api.get_streets_by_city(
                streets_by_city_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_STREETS_BY_CITY, api_call
        )

    async def get_streets_by_id(
        self, request: StreetsByIdRequest
    ) -> StreetsByIdResponse:
        """Улицы по ids или classifierIds (correlation_id в ответе optional)."""

        async def api_call() -> StreetsByIdResponse:
            api = await self.get_addresses_api()
            return await api.get_streets_by_id(streets_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_STREETS_BY_ID, api_call
        )
```

`iikocloud/mixins/addresses/helpers.py`:

```python
"""Addresses helpers mixin — convenience-методы (заготовка)."""

from iikocloud.mixins.addresses.core import AddressesCoreMixin


class AddressesHelpersMixin(AddressesCoreMixin):
    """Публичный addresses mixin (helpers появятся позже)."""
```

В `iikocloud/api_client_manager.py`: импорт `AddressesHelpersMixin`, в MRO последним перед `_ManagerBase` (или после `DraftsHelpersMixin,`), docstring пополнить `addresses`.

- [ ] **Step 4: Run — PASS + качество**: unit +4 passed, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/addresses iikocloud/api_client_manager.py tests/unit/test_addresses.py
git commit -m "feat(addresses): cities/regions/streets geo-directory wrappers"
```

---

### Task 3: Integration read (секция read)

**Files:**
- Create: `tests/integration/addresses/__init__.py` (пустой)
- Create: `tests/integration/addresses/test_read.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id` (read-секция по умолчанию — маркеров не надо)

- [ ] **Step 1: Тест**

`tests/integration/addresses/test_read.py`:

```python
"""Интеграционные read-тесты Addresses API (read-секция).

Запуск:
    uv run pytest tests/integration/addresses -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    CitiesRequest,
    RegionsRequest,
    StreetsByCityRequest,
    StreetsByIdRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


@pytest.fixture
async def first_city_id(
    manager: IikoCloudApiClientManager, organization_id: UUID
) -> UUID:
    """Первый город организации (skip, если городов нет)."""
    response = await manager.get_cities(
        CitiesRequest(organization_ids=[organization_id])
    )
    cities = [
        city
        for org in response.cities or []
        for city in org.items or []
        if not city.is_deleted
    ]
    if not cities:
        pytest.skip("Нет городов у организации read-стенда")
    return cities[0].id


class TestAddressesRead:
    async def test_get_cities_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_cities(
            CitiesRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.cities is not None

    async def test_get_regions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_regions(
            RegionsRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.regions is not None

    async def test_get_streets_by_city_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        first_city_id: UUID,
    ) -> None:
        response = await manager.get_streets_by_city(
            StreetsByCityRequest(
                organization_id=organization_id, city_id=first_city_id
            )
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.streets is not None

    async def test_get_streets_by_id_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        first_city_id: UUID,
    ) -> None:
        streets_response = await manager.get_streets_by_city(
            StreetsByCityRequest(
                organization_id=organization_id, city_id=first_city_id
            )
        )
        streets = [
            s for s in streets_response.streets or [] if not s.is_deleted
        ]
        if not streets:
            pytest.skip("Нет улиц в городе read-стенда")

        response = await manager.get_streets_by_id(
            StreetsByIdRequest(
                organization_id=organization_id, ids=[streets[0].id]
            )
        )

        assert response is not None
        assert response.streets is not None
        if response.streets:
            street = response.streets[0]
            assert street.id is not None
            assert street.city_id is not None
            assert isinstance(street.street_name, str)
```

ВНИМАНИЕ реализатору: фикстура `first_city_id` async — оформи через
`@pytest_asyncio.fixture(loop_scope="session")` (импорт `pytest_asyncio`),
как в соседних пакетах; в коде выше оставлен обычный декоратор для краткости —
приведи к конвенции проекта.

- [ ] **Step 2: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/addresses -q -rs`
Expected: PASS (или skip с явной причиной: нет городов/улиц на стенде).

- [ ] **Step 3: Регрессия + качество**: unit suite, ruff/mypy чисто
- [ ] **Step 4: Commit**

```bash
git add tests/integration/addresses
git commit -m "test: addresses read integration tests"
```
