"""Интеграционные read-тесты Menu API.

Запуск:
    uv run pytest tests/integration/menu -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest

from iikocloud import IikoCloudApiClientManager, MenuTooEarly

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


class TestMenuWindows:
    """Окна чтения меню против реального API (выпуск 0.3.0): одно чтение,
    второе — «рано»."""

    async def test_a_second_menu_right_away_is_told_when_without_waiting(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Меню нового адреса читается; второе сразу — ``MenuTooEarly`` с числом секунд."""
        import asyncio

        from iikocloud_client import MenuRequestV3

        menus = (await manager.get_external_menus()).external_menus or []
        if not menus:
            pytest.skip("у ключа нет внешних меню")
        request = MenuRequestV3(
            external_menu_id=str(menus[0].id), organization_id=organization_id
        )
        menu = await manager.get_external_menu_v3_by_id(request)
        assert menu is not None
        with pytest.raises(MenuTooEarly) as early:
            await asyncio.wait_for(manager.get_external_menu_v3_by_id(request), timeout=2)
        assert early.value.seconds > 0
        assert manager.menu_state()["paused_for_sec"] == 0

