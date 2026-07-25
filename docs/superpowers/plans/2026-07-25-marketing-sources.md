# MarketingSources Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обёртка над `get_marketing_sources` + unit- и read integration-тесты.

**Architecture:** Новый домен `iikocloud/mixins/marketing_sources/` (`core.py` + `helpers.py`-заготовка), регистрация через `MarketingSourcesHelpersMixin` в MRO.

**Spec:** `docs/superpowers/specs/2026-07-25-marketing-sources-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- `ApiMethod` value == snake_case имени метода SDK (Locked Names).
- Rate limit: `get_marketing_sources` — 1/60s.
- SDK kwarg: `marketing_sources_request`.
- Проверки качества: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура

**Files:**
- Modify: `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: `ApiMethod.GET_MARKETING_SOURCES`; `async _ManagerBase.get_marketing_sources_api() -> MarketingSourcesApi`

- [ ] **Step 1: Failing test**

```python
def test_marketing_sources_method_has_limits() -> None:
    """get_marketing_sources есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    config = limits.for_method(ApiMethod("get_marketing_sources"))
    assert config.max_requests / config.time_window_seconds == pytest.approx(
        1 / 60.0
    )
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация**

В `_base.py`: импорт `MarketingSourcesApi` (алфавитно); в `ApiMethod` секция `# Marketing Sources` со значением `GET_MARKETING_SOURCES = "get_marketing_sources"`; поле в `MethodRateLimits`; слот `_marketing_sources_api: MarketingSourcesApi | None` + геттер. В `api_client_manager.py.__init__`: слот + импорт. В `config_reader.py` (комментарий `# Marketing Sources`): поле `get_marketing_sources` 1/60.0. В `config.example.yml`: 1 блок.

- [ ] **Step 4: Run — PASS + качество**: unit +1, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/_base.py iikocloud/api_client_manager.py iikocloud/config_reader.py config.example.yml tests/unit/test_config_reader.py
git commit -m "feat: register rate limit and lazy client for marketing sources"
```

---

### Task 2: Core + helpers-заготовка + регистрация

**Files:**
- Create: `iikocloud/mixins/marketing_sources/{__init__,core,helpers}.py`
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO + docstring)
- Test: `tests/unit/test_marketing_sources.py`

**Interfaces:**
- Produces: `get_marketing_sources(request: MarketingSourcesRequest) -> MarketingSourcesResponse`

- [ ] **Step 1: Failing test**

`tests/unit/test_marketing_sources.py`:

```python
"""Unit tests for MarketingSources domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import MarketingSourcesRequest, MarketingSourcesResponse

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_marketing_sources_api"


async def test_get_marketing_sources_delegates() -> None:
    """get_marketing_sources проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=MarketingSourcesResponse)
    mock_api.get_marketing_sources = AsyncMock(return_value=mock_response)

    request = MarketingSourcesRequest(organization_ids=[ORG_ID])
    result = await manager.get_marketing_sources(request)

    assert result is mock_response
    mock_api.get_marketing_sources.assert_awaited_once_with(
        marketing_sources_request=request
    )
```

- [ ] **Step 2: Run — FAIL** (AttributeError)

- [ ] **Step 3: Реализация**

`__init__.py` — реэкспорты по конвенции. `core.py`:

```python
"""MarketingSources core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import MarketingSourcesRequest, MarketingSourcesResponse

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class MarketingSourcesCoreMixin(_ManagerBase):
    """Core-методы MarketingSources API (read-only, iiko >= 7.2.5)."""

    async def get_marketing_sources(
        self,
        request: MarketingSourcesRequest,
    ) -> MarketingSourcesResponse:
        """Справочник источников маркетинга организаций."""

        async def api_call() -> MarketingSourcesResponse:
            api = await self.get_marketing_sources_api()
            return await api.get_marketing_sources(
                marketing_sources_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_MARKETING_SOURCES, api_call
        )
```

`helpers.py` — заготовка `MarketingSourcesHelpersMixin(MarketingSourcesCoreMixin)` с docstring. В `api_client_manager.py`: импорт, MRO, docstring (`marketing_sources`).

- [ ] **Step 4: Run — PASS + качество**: unit +1, ruff/mypy чисто
- [ ] **Step 5: Commit**

```bash
git add iikocloud/mixins/marketing_sources iikocloud/api_client_manager.py tests/unit/test_marketing_sources.py
git commit -m "feat(marketing-sources): get_marketing_sources wrapper"
```

---

### Task 3: Integration read (секция read)

**Files:**
- Create: `tests/integration/dictionaries/test_marketing_sources.py`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id` (read-секция — данные есть, подтверждено пользователем)

- [ ] **Step 1: Тест**

`tests/integration/dictionaries/test_marketing_sources.py`:

```python
"""Интеграционный read-тест MarketingSources API (read-секция).

Запуск:
    uv run pytest tests/integration/dictionaries/test_marketing_sources.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import MarketingSourcesRequest

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestGetMarketingSources:
    async def test_get_marketing_sources_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_marketing_sources(
            MarketingSourcesRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.marketing_sources is not None
        if response.marketing_sources:
            source = response.marketing_sources[0]
            assert source.id is not None
            assert isinstance(source.name, str)
            assert source.organization_id is not None
```

- [ ] **Step 2: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/dictionaries/test_marketing_sources.py -q -rs`
Expected: PASS.

- [ ] **Step 3: Регрессия + качество**: unit suite, ruff/mypy чисто
- [ ] **Step 4: Commit**

```bash
git add tests/integration/dictionaries/test_marketing_sources.py
git commit -m "test: marketing sources read integration test"
```
