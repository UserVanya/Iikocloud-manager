# Operations Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Обёртка над `get_command_status` + helper `wait_command` + unit- и danger_write integration-тесты.

**Spec:** `docs/superpowers/specs/2026-07-25-operations-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response (полиморф по `state`).
- Locked Names; лимит `get_command_status` — 60/60s (polling-метод).
- SDK kwarg: `get_command_status_request`.
- `wait_command`: терминальные состояния Success/Error → возврат статуса; HTTP 410 → `IikoCloudApiException`; timeout → `TimeoutError`.
- Гейты: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура

**Files:** Modify `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`; Test `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: `ApiMethod.GET_COMMAND_STATUS`; `async _ManagerBase.get_operations_api() -> OperationsApi`

- [ ] **Step 1: Failing test**

```python
def test_get_command_status_has_limits() -> None:
    """get_command_status есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    config = limits.for_method(ApiMethod("get_command_status"))
    assert config.max_requests / config.time_window_seconds == pytest.approx(
        60 / 60.0
    )
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — импорт `OperationsApi`; `GET_COMMAND_STATUS = "get_command_status"`; поле в `MethodRateLimits`; слот `_operations_api` + геттер; слот+импорт в `__init__`; поле в settings (60/60); блок в `config.example.yml`.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat: register rate limit and lazy client for operations`

---

### Task 2: Core + helper wait_command + регистрация

**Files:** Create `iikocloud/mixins/operations/{__init__,core,helpers}.py`; Modify `iikocloud/api_client_manager.py`; Test `tests/unit/test_operations.py`

**Interfaces:**
- Produces:
  - `get_command_status(request: GetCommandStatusRequest) -> SuccessCommandStatus | InProgressCommandStatus | ErrorCommandStatus` (SDK возвращает `GetCommandStatusResponse` — фактический родитель; типизация по SDK)
  - `async wait_command(correlation_id: str | UUID, organization_id: str | UUID, *, timeout: float = 30.0, interval: float = 2.0) -> SuccessCommandStatus | ErrorCommandStatus`

Проверить при реализации: точное имя базового класса ответа в SDK (`GetCommandStatusResponse` — дискриминатор-база) и поле `state` у подклассов; `ErrorCommandStatus.error_reason`.

- [ ] **Step 1: Failing tests**

`tests/unit/test_operations.py`:

```python
"""Unit tests for Operations domain mixins."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from iikocloud_client import (
    ErrorCommandStatus,
    GetCommandStatusRequest,
    InProgressCommandStatus,
    SuccessCommandStatus,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_operations_api"


async def test_get_command_status_delegates() -> None:
    """get_command_status проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=SuccessCommandStatus)
    mock_api.get_command_status = AsyncMock(return_value=mock_response)

    request = GetCommandStatusRequest(
        organization_id=ORG_ID, correlation_id=ORG_ID
    )
    result = await manager.get_command_status(request)

    assert result is mock_response
    mock_api.get_command_status.assert_awaited_once_with(
        get_command_status_request=request
    )


async def test_wait_command_success_immediately() -> None:
    """wait_command: Success с первого опроса."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        return_value=SuccessCommandStatus(state="Success")
    )

    result = await manager.wait_command(ORG_ID, ORG_ID, interval=0.01)

    assert isinstance(result, SuccessCommandStatus)


async def test_wait_command_in_progress_then_success() -> None:
    """wait_command: InProgress -> Success."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        side_effect=[
            InProgressCommandStatus(state="InProgress"),
            SuccessCommandStatus(state="Success"),
        ]
    )

    result = await manager.wait_command(ORG_ID, ORG_ID, interval=0.01)

    assert isinstance(result, SuccessCommandStatus)
    assert mock_api.get_command_status.await_count == 2


async def test_wait_command_error_status_returned() -> None:
    """wait_command: Error-статус возвращается вызывающему."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        return_value=ErrorCommandStatus(state="Error", error_reason="boom")
    )

    result = await manager.wait_command(ORG_ID, ORG_ID, interval=0.01)

    assert isinstance(result, ErrorCommandStatus)
    assert result.error_reason == "boom"


async def test_wait_command_timeout() -> None:
    """wait_command: timeout -> TimeoutError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        return_value=InProgressCommandStatus(state="InProgress")
    )

    with pytest.raises(TimeoutError, match="wait_command"):
        await manager.wait_command(
            ORG_ID, ORG_ID, timeout=0.05, interval=0.01
        )
```

- [ ] **Step 2: Run — FAIL** (AttributeError)

- [ ] **Step 3: Реализация**

`__init__.py` — реэкспорты. `core.py`:

```python
"""Operations core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import GetCommandStatusRequest, GetCommandStatusResponse

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class OperationsCoreMixin(_ManagerBase):
    """Core-методы Operations API (статусы асинхронных команд)."""

    async def get_command_status(
        self,
        request: GetCommandStatusRequest,
    ) -> GetCommandStatusResponse:
        """Статус команды по correlation_id (Success/InProgress/Error).

        HTTP 410 — correlationId устарел, polling прекращать.
        """

        async def api_call() -> GetCommandStatusResponse:
            api = await self.get_operations_api()
            return await api.get_command_status(
                get_command_status_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_COMMAND_STATUS, api_call
        )
```

(если фактический класс ответа в SDK называется иначе — взять имя из SDK; импорт `GetCommandStatusResponse` проверен: существует как дискриминатор-база.)

`helpers.py`:

```python
"""Operations helpers mixin — polling статусов команд."""

import asyncio
import time
from uuid import UUID

from iikocloud_client import (
    ErrorCommandStatus,
    GetCommandStatusRequest,
    GetCommandStatusResponse,
    InProgressCommandStatus,
    SuccessCommandStatus,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.operations.core import OperationsCoreMixin

_TERMINAL = (SuccessCommandStatus, ErrorCommandStatus)


class OperationsHelpersMixin(OperationsCoreMixin):
    """Публичный operations mixin с polling-helpers."""

    async def wait_command(
        self,
        correlation_id: str | UUID,
        organization_id: str | UUID,
        *,
        timeout: float = 30.0,
        interval: float = 2.0,
    ) -> SuccessCommandStatus | ErrorCommandStatus:
        """Дождаться терминального статуса команды (Success/Error).

        Raises:
            TimeoutError: статус не стал терминальным за timeout
        """
        request = GetCommandStatusRequest(
            organization_id=as_uuid(organization_id),
            correlation_id=as_uuid(correlation_id),
        )
        deadline = time.monotonic() + timeout
        last_state = "unknown"
        while True:
            status = await self.get_command_status(request)
            if isinstance(status, _TERMINAL):
                return status
            last_state = getattr(status, "state", last_state)
            if time.monotonic() + interval > deadline:
                raise TimeoutError(
                    f"wait_command: за {timeout}s статус остался {last_state}"
                )
            await asyncio.sleep(interval)
```

Проверить при реализации: `asyncio.sleep` мокать не нужно — interval=0.01 в тестах; `GetCommandStatusResponse` — базовый тип; isinstance-проверки по подклассам. HTTP 410: ApiException со status=410 — перехватить в `wait_command` и перевести в понятное исключение проекта (`IikoCloudApiException` из `iikocloud/exceptions.py` — проверить наличие; если нет подходящего, оставить проброс SDK-исключения и задокументировать).

В `api_client_manager.py`: импорт, MRO, docstring (`operations`).

- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat(operations): get_command_status and wait_command polling helper`

---

### Task 3: Integration danger_write (реальная команда стоп-листа)

**Files:** Create `tests/integration/operations/{__init__,test_status.py}`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`, `live_terminal_group_id`, `product`; стоп-лист методы menu-домена

- [ ] **Step 1: Тест**

`tests/integration/operations/test_status.py`:

```python
"""Danger_write-тест Operations (write-секция).

stop_list add (команда) -> get_command_status -> wait_command -> cleanup.

Запуск:
    uv run pytest tests/integration/operations -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    AddProductsToStopListItem,
    AddProductsToStopListRequest,
    ClearStopListRequest,
    ErrorCommandStatus,
    GetCommandStatusRequest,
    SuccessCommandStatus,
)

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestCommandStatus:
    async def test_status_and_wait_for_stop_list_command(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        product: tuple[UUID, float],
    ) -> None:
        product_id, _ = product
        try:
            add_response = await manager.add_products_to_stop_list(
                AddProductsToStopListRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    items=[
                        AddProductsToStopListItem(
                            product_id=product_id, balance=0.0
                        )
                    ],
                )
            )
            correlation_id = add_response.correlation_id
            assert correlation_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # get_command_status — валидный ответ (InProgress или Success)
            status = await manager.get_command_status(
                GetCommandStatusRequest(
                    organization_id=organization_id,
                    correlation_id=correlation_id,
                )
            )
            assert status is not None
            assert getattr(status, "state", None) in (
                "Success",
                "InProgress",
                "Error",
            )

            # wait_command — терминальный статус
            final = await manager.wait_command(
                correlation_id, organization_id, timeout=60.0
            )
            assert isinstance(
                final, (SuccessCommandStatus, ErrorCommandStatus)
            )
            if isinstance(final, ErrorCommandStatus):
                pytest.fail(f"Команда стоп-листа завершилась ошибкой: {final.error_reason}")

        finally:
            try:
                await asyncio.sleep(_API_PAUSE_SEC)
                await manager.clear_stop_list(
                    ClearStopListRequest(
                        organization_id=organization_id,
                        terminal_group_id=live_terminal_group_id,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("clear_stop_list cleanup: %s", exc)
```

- [ ] **Step 2: Прогон живьём** — `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/operations -q -rs`
- [ ] **Step 3: Регрессия + гейты**
- [ ] **Step 4: Commit** `test: command status and wait_command against real stop-list command`
