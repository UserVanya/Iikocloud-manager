"""Пример использования iikocloud модуля."""

import asyncio
from pprint import pprint

from iikocloud_client import OrganizationsGetOrganizationsRequest

from iikocloud import IikoCloudApiClientManager, get_iikocloud_config


async def main() -> None:
    """Основная функция примера."""
    print("IikoCloud Manager Example")

    # Получаем конфигурацию из YAML-файла
    # Путь к файлу указывается в переменной IIKOCLOUD_CONFIG
    config = get_iikocloud_config()

    # Создаём менеджер из конфигурации
    manager = await IikoCloudApiClientManager.from_config(config)

    try:
        # Получаем список организаций
        request = OrganizationsGetOrganizationsRequest()
        response = await manager.organizations(request)
        pprint(response)
    finally:
        # Закрываем все соединения
        await IikoCloudApiClientManager.close_all()


if __name__ == "__main__":
    asyncio.run(main())
