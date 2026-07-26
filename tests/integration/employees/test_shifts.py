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
