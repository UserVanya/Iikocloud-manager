# Employees Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Обёртки над 10 методами `EmployeesApi` + unit- и integration-тесты (structure + danger_write смены).

**Spec:** `docs/superpowers/specs/2026-07-25-employees-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- Locked Names: `ApiMethod` value == snake_case SDK method == поле в `MethodRateLimitsSettings`/`MethodRateLimits`.
- Лимиты: `get_couriers`, `get_couriers_by_role`, `get_employee_info` — 1/60s; `get_active_courier_locations`, `get_active_courier_locations_by_terminal`, `get_courier_location_history`, `get_personal_session_info`, `get_terminal_groups_of_employee` — 10/60s; `open_personal_session`, `close_personal_session` — 100/60s.
- SDK kwargs: `couriers_request` (get_couriers И get_active_courier_locations — одна модель), `couriers_and_check_role_request`, `employee_info_request`, `active_courier_locations_by_terminal_group_request`, `courier_locations_by_time_offset_request`, `get_personal_session_info_request`, `get_terminal_groups_of_employee_request`, `open_personal_session_request`, `close_personal_session_request`.
- Гейты: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

---

### Task 1: Инфраструктура

**Files:** Modify `iikocloud/mixins/_base.py`, `iikocloud/api_client_manager.py` (слот), `iikocloud/config_reader.py`, `config.example.yml`; Test `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: 10 `ApiMethod`; `async _ManagerBase.get_employees_api() -> EmployeesApi`

- [ ] **Step 1: Failing test**

```python
def test_employees_methods_have_limits() -> None:
    """10 методов employees есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "get_couriers": 1 / 60.0,
        "get_couriers_by_role": 1 / 60.0,
        "get_employee_info": 1 / 60.0,
        "get_active_courier_locations": 10 / 60.0,
        "get_active_courier_locations_by_terminal": 10 / 60.0,
        "get_courier_location_history": 10 / 60.0,
        "get_personal_session_info": 10 / 60.0,
        "get_terminal_groups_of_employee": 10 / 60.0,
        "open_personal_session": 100 / 60.0,
        "close_personal_session": 100 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)
```

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — импорт `EmployeesApi`; секция `# Employees` в `ApiMethod` (10 значений SCREAMING_CASE → locked names из теста); 10 полей `RateLimitConfig` в `MethodRateLimits`; слот `_employees_api: EmployeesApi | None` + геттер `get_employees_api()` (паттерн соседних); слот+импорт в `api_client_manager.py.__init__`; секция `# Employees` с 10 полями в `MethodRateLimitsSettings`; 10 блоков в `config.example.yml`.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat: register rate limits and lazy client for employees`

---

### Task 2: Core + helpers-заготовка + регистрация

**Files:** Create `iikocloud/mixins/employees/{__init__,core,helpers}.py`; Modify `iikocloud/api_client_manager.py`; Test `tests/unit/test_employees.py`

**Interfaces:**
- Produces: `EmployeesCoreMixin` (10 методов); `EmployeesHelpersMixin(EmployeesCoreMixin)` — заготовка

Минимальные модели (проверены; `u = ORG_ID`):

```python
CouriersRequest(organization_ids=[u])
CouriersAndCheckRoleRequest(organization_ids=[u], roles_to_check=["R"])
EmployeeInfoRequest(id=u, organization_id=u)
ActiveCourierLocationsByTerminalGroupRequest(organization_id=u, terminal_group_id=u)
CourierLocationsByTimeOffsetRequest(organization_ids=[u], offset_in_seconds=60)
GetPersonalSessionInfoRequest(employee_id=u, organization_id=u, terminal_group_id=u)
GetTerminalGroupsOfEmployeeRequest(employee_id=u)
OpenPersonalSessionRequest(employee_id=u, organization_id=u, terminal_group_id=u)
ClosePersonalSessionRequest(employee_id=u, organization_id=u, terminal_group_id=u)
```

- [ ] **Step 1: Failing tests**

`tests/unit/test_employees.py`:

```python
"""Unit tests for Employees domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    ActiveCourierLocationsByTerminalGroupRequest,
    ActiveCourierLocationsResponse,
    ChangePersonalSessionResponse,
    ClosePersonalSessionRequest,
    CourierLocationsByTimeOffsetRequest,
    CourierLocationsByTimeOffsetResponse,
    CouriersAndCheckRoleRequest,
    CouriersRequest,
    EmployeeInfoRequest,
    EmployeeInfoResponse,
    EmployeesResponse,
    EmployeesWithRoleSignResponse,
    GetPersonalSessionInfoRequest,
    GetPersonalSessionInfoResponse,
    GetTerminalGroupsOfEmployeeRequest,
    GetTerminalGroupsOfEmployeeResponse,
    OpenPersonalSessionRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_employees_api"

METHODS: list[tuple[str, object, str, type]] = [
    ("get_couriers", CouriersRequest(organization_ids=[ORG_ID]), "couriers_request", EmployeesResponse),
    ("get_couriers_by_role", CouriersAndCheckRoleRequest(organization_ids=[ORG_ID], roles_to_check=["R"]), "couriers_and_check_role_request", EmployeesWithRoleSignResponse),
    ("get_employee_info", EmployeeInfoRequest(id=ORG_ID, organization_id=ORG_ID), "employee_info_request", EmployeeInfoResponse),
    ("get_active_courier_locations", CouriersRequest(organization_ids=[ORG_ID]), "couriers_request", ActiveCourierLocationsResponse),
    ("get_active_courier_locations_by_terminal", ActiveCourierLocationsByTerminalGroupRequest(organization_id=ORG_ID, terminal_group_id=ORG_ID), "active_courier_locations_by_terminal_group_request", ActiveCourierLocationsResponse),
    ("get_courier_location_history", CourierLocationsByTimeOffsetRequest(organization_ids=[ORG_ID], offset_in_seconds=60), "courier_locations_by_time_offset_request", CourierLocationsByTimeOffsetResponse),
    ("get_personal_session_info", GetPersonalSessionInfoRequest(employee_id=ORG_ID, organization_id=ORG_ID, terminal_group_id=ORG_ID), "get_personal_session_info_request", GetPersonalSessionInfoResponse),
    ("get_terminal_groups_of_employee", GetTerminalGroupsOfEmployeeRequest(employee_id=ORG_ID), "get_terminal_groups_of_employee_request", GetTerminalGroupsOfEmployeeResponse),
    ("open_personal_session", OpenPersonalSessionRequest(employee_id=ORG_ID, organization_id=ORG_ID, terminal_group_id=ORG_ID), "open_personal_session_request", ChangePersonalSessionResponse),
    ("close_personal_session", ClosePersonalSessionRequest(employee_id=ORG_ID, organization_id=ORG_ID, terminal_group_id=ORG_ID), "close_personal_session_request", ChangePersonalSessionResponse),
]


@pytest.mark.parametrize(("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS)
async def test_employees_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 10 методов проксируют response с request-моделью."""
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

`__init__.py` — реэкспорты по конвенции. `core.py` — класс `EmployeesCoreMixin(_ManagerBase)` с 10 методами по единому шаблону (см. любой существующий домен, напр. `iikocloud/mixins/addresses/core.py`): inner `api_call` → lazy-геттер `get_employees_api()` → `execute_with_retry(ApiMethod.X, api_call)`. SDK kwargs — из таблицы теста. Docstring каждого метода — 1 строка по смыслу:
- get_couriers — «Сотрудники-курьеры организаций»
- get_couriers_by_role — «Курьеры с проверкой ролей»
- get_employee_info — «Информация о сотруднике по id»
- get_active_courier_locations — «Локации активных курьеров»
- get_active_courier_locations_by_terminal — «Локации курьеров терминала»
- get_courier_location_history — «История координат курьеров (offset в секундах)»
- get_personal_session_info — «Открыта ли личная сессия сотрудника»
- get_terminal_groups_of_employee — «Терминальные группы с открытой сессией сотрудника»
- open_personal_session — «Открыть смену (команда; role_id — только если ресторан использует роли)»
- close_personal_session — «Закрыть смену (команда)»

`helpers.py` — заготовка `EmployeesHelpersMixin(EmployeesCoreMixin)`. В `api_client_manager.py`: импорт, MRO, docstring (`employees`).

- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat(employees): 10 courier/shift/info wrappers`

---

### Task 3: Integration (structure + danger_write смены)

**Files:** Create `tests/integration/employees/{__init__,test_read.py,test_shifts.py}`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`, `live_terminal_group_id` (root conftest); ключ `employee_id` из write-секции config.test.yml (есть локально)

- [ ] **Step 1: Тесты**

`test_read.py` (маркер `test_server`):

```python
"""Structure-only read-тесты Employees (write-секция через test_server)."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    CourierLocationsByTimeOffsetRequest,
    CouriersRequest,
    EmployeeInfoRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestEmployeesRead:
    async def test_get_couriers_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.get_couriers(
            CouriersRequest(organization_ids=[organization_id])
        )
        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.employees is not None

    async def test_get_employee_info_by_first_courier(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        couriers = await manager.get_couriers(
            CouriersRequest(organization_ids=[organization_id])
        )
        employees = [
            e for org in couriers.employees or [] for e in org.items or []
        ]
        if not employees:
            pytest.skip("Нет сотрудников на write-стенде")
        info = await manager.get_employee_info(
            EmployeeInfoRequest(
                id=employees[0].id, organization_id=organization_id
            )
        )
        assert info is not None
        assert info.employee_info is not None
        assert info.employee_info.id == employees[0].id

    async def test_courier_location_history_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.get_courier_location_history(
            CourierLocationsByTimeOffsetRequest(
                organization_ids=[organization_id], offset_in_seconds=3600
            )
        )
        assert response is not None
        assert response.courier_locations is not None
```

`test_shifts.py` (маркер `danger_write`; employee_id из конфига — паттерн `_write_config_key` из drafts):

```python
"""Danger_write-тест смен Employees (write-секция).

Цикл: is_open -> open -> is_open (True) -> close (finally).
Если сессия уже открыта до теста — skip (не трогаем чужую смену).

Запуск:
    uv run pytest tests/integration/employees/test_shifts.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
import os
from uuid import UUID

import pytest
from iikocloud_client import (
    ClosePersonalSessionRequest,
    GetPersonalSessionInfoRequest,
    OpenPersonalSessionRequest,
)
from yaml import CSafeLoader
from yaml import load as yaml_load

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


def _write_config_key(key: str) -> str | None:
    from functools import lru_cache

    @lru_cache
    def _load(path: str):
        with open(path, "rb") as file:
            return yaml_load(file, Loader=CSafeLoader)

    path = os.getenv("IIKOCLOUD_TEST_CONFIG")
    if not path:
        return None
    value = (_load(path).get("write") or {}).get(key)
    return str(value) if value else None


@pytest.fixture
def shift_employee_id() -> UUID:
    employee_id = _write_config_key("employee_id")
    if not employee_id:
        pytest.skip("В write-секции config.test.yml не задан employee_id")
    return UUID(employee_id)


class TestPersonalSession:
    async def test_open_and_close_session(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
        shift_employee_id: UUID,
    ) -> None:
        async def _is_open() -> bool | None:
            resp = await manager.get_personal_session_info(
                GetPersonalSessionInfoRequest(
                    employee_id=shift_employee_id,
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                )
            )
            return resp.is_session_opened

        opened_before = await _is_open()
        if opened_before:
            pytest.skip("Сессия сотрудника уже открыта — не трогаем")

        opened_by_test = False
        try:
            open_resp = await manager.open_personal_session(
                OpenPersonalSessionRequest(
                    employee_id=shift_employee_id,
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                )
            )
            assert open_resp is not None
            assert open_resp.error is None
            opened_by_test = True

            await asyncio.sleep(_API_PAUSE_SEC)
            assert await _is_open() is True

        finally:
            if opened_by_test:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.close_personal_session(
                        ClosePersonalSessionRequest(
                            employee_id=shift_employee_id,
                            organization_id=organization_id,
                            terminal_group_id=live_terminal_group_id,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Close session cleanup failed: %s", exc)
```

- [ ] **Step 2: Прогон живьём**

Run: `IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/employees -q -rs`
Expected: PASS или skip с явной причиной (сессия открыта / фронт офлайн).

- [ ] **Step 3: Регрессия + гейты**
- [ ] **Step 4: Commit** `test: employees structure and personal session lifecycle`
