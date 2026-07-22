"""Интеграционные read-тесты Terminal Groups API.

Запуск:
    uv run pytest tests/integration/terminal_groups -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    TerminalGroupsIsAliveRequest,
    TerminalGroupsRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


def _first_terminal_group_id(groups_response: object) -> UUID | None:
    """Найти id первой терминальной группы в ответе (или None)."""
    terminal_groups = getattr(groups_response, "terminal_groups", None)
    if not terminal_groups:
        return None
    for org_groups in terminal_groups:
        items = getattr(org_groups, "items", None) or []
        if items:
            return items[0].id
    return None


class TestGetTerminalGroups:
    """get_terminal_groups / availability против реального API."""

    async def test_get_terminal_groups_by_organization(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Helper возвращает структуру terminal_groups + correlation_id."""
        response = await manager.get_terminal_groups_by_organization(
            organization_id
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert hasattr(response, "terminal_groups")
        assert response.terminal_groups is not None

    async def test_get_terminal_groups_with_request(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """get_terminal_groups принимает полный TerminalGroupsRequest."""
        request = TerminalGroupsRequest(
            organization_ids=[organization_id],
            include_disabled=True,
        )
        response = await manager.get_terminal_groups(request)

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.terminal_groups is not None

    async def test_check_terminal_groups_availability(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """check_terminal_groups_availability для динамически найденной группы."""
        groups_response = await manager.get_terminal_groups_by_organization(
            organization_id
        )
        group_id = _first_terminal_group_id(groups_response)
        if group_id is None:
            pytest.skip("Нет доступных терминальных групп")

        request = TerminalGroupsIsAliveRequest(
            organization_ids=[organization_id],
            terminal_group_ids=[group_id],
        )
        response = await manager.check_terminal_groups_availability(request)

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert hasattr(response, "is_alive_status")
        assert response.is_alive_status is not None
