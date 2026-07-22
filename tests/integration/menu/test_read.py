"""Интеграционные read-тесты Menu API.

Запуск:
    uv run pytest tests/integration/menu -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestGetExternalMenus:
    """get_external_menus против реального API."""

    async def test_get_external_menus_returns_structure(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """get_external_menus возвращает correlation_id и список меню."""
        response = await manager.get_external_menus()

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert hasattr(response, "external_menus")
        # Список может быть пустым на стенде без внешних меню
        assert response.external_menus is not None
        # Динамическое обнаружение: если меню есть — id/name валидны
        if response.external_menus:
            menu = response.external_menus[0]
            assert menu.id is not None
            assert isinstance(menu.name, str)


class TestGetStopLists:
    """get_stop_lists против реального API."""

    async def test_get_stop_lists_by_organization(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Helper возвращает стоп-листы организации."""
        response = await manager.get_stop_lists_by_organization(organization_id)

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert hasattr(response, "terminal_group_stop_lists")
        assert response.terminal_group_stop_lists is not None
