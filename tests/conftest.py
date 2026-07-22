"""Общие фикстуры для тестов.

Содержит фикстуры, используемые в различных тестовых модулях.
"""

from __future__ import annotations

import random
import re
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID

import pytest

from iikocloud.rate_limiter import GlobalRateLimiter

if TYPE_CHECKING:
    from iikocloud.api_client_manager import IikoCloudApiClientManager

# Константы для тестов Customer API
EXISTING_CUSTOMER_PHONE = "+79858038700"
NOT_FOUND_CUSTOMER_PHONE = "+71234567890"

# Паттерны для поиска организации и меню для Menu API тестов
MENU_ORG_PATTERN = re.compile(r"мигуста", re.IGNORECASE)
MENU_NAME_PATTERN = re.compile(r"мигуста|мигуста|доставка", re.IGNORECASE)


def generate_random_phone() -> str:
    """Генерирует случайный номер телефона для тестов."""
    return f"+7{random.randint(1000000000, 1999999999)}"


# ========== Интеграционные фикстуры ==========


@pytest.fixture
async def manager() -> AsyncGenerator[IikoCloudApiClientManager, None]:
    """Создать менеджер из реальной конфигурации."""
    from iikocloud.api_client_manager import IikoCloudApiClientManager
    from iikocloud.config_reader import get_iikocloud_config
    from iikocloud.token_manager import TokenManager

    config = get_iikocloud_config()
    mgr = await IikoCloudApiClientManager.from_config(config)
    yield mgr
    # Cleanup после каждого теста
    await IikoCloudApiClientManager.close_all()
    GlobalRateLimiter.reset_instance()
    await TokenManager.close_all()


@pytest.fixture
async def organization_id(
    manager: IikoCloudApiClientManager,
) -> UUID:
    """Получить ID первой организации для тестов."""
    #from iikocloud_client import OrganizationsGetOrganizationsRequest

    # request = OrganizationsGetOrganizationsRequest()
    # response = await manager.get_organizations(request)
    # assert len(response.organizations) > 0, "Нет доступных организаций"
    # return response.organizations[0].id
    return UUID("815bb8fd-b393-477a-8abc-fb962ab408d6")


@pytest.fixture
async def menu_test_organization_id(
    manager: IikoCloudApiClientManager,
) -> UUID:
    """Получить ID организации, содержащей 'мигуста' в названии.

    Используется для тестов Menu API.
    """
    return UUID("815bb8fd-b393-477a-8abc-fb962ab408d6")
    # from iikocloud_client import OrganizationsGetOrganizationsRequest

    # request = OrganizationsGetOrganizationsRequest()
    # response = await manager.get_organizations(request)
    # assert len(response.organizations) > 0, "Нет доступных организаций"

    # # Ищем организацию с "мигуста" в названии (case-insensitive)
    # for org in response.organizations:
    #     if org.name and MENU_ORG_PATTERN.search(org.name):
    #         return org.id

    # # Если не нашли — пропускаем тест
    # pytest.skip("Не найдена организация с 'мигуста' в названии")


@pytest.fixture
async def menu_id(
    manager: IikoCloudApiClientManager,
) -> str:
    """Получить ID меню, содержащего 'мигуста|мигуста|доставка' в названии.

    Используется для тестов Menu API.
    """
    # menus_response = await manager.get_external_menus()

    # if not menus_response.external_menus or len(menus_response.external_menus) == 0:
    #     pytest.skip("Нет доступных внешних меню")

    # # Ищем меню с подходящим названием (case-insensitive)
    # for menu in menus_response.external_menus:
    #     if menu.name and MENU_NAME_PATTERN.search(menu.name) and menu.id:
    #         return str(menu.id)

    # # Если не нашли — пропускаем тест
    # pytest.skip("Не найдено меню с 'мигуста|мигуста|доставка' в названии")

    return "23311"
