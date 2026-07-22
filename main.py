"""Пример использования iikocloud модуля."""

import asyncio

from iikocloud import IikoCloudApiClientManager, get_iikocloud_config


async def main() -> None:
    """Основная функция примера."""
    config = get_iikocloud_config()
    manager = await IikoCloudApiClientManager.from_config(config)
    try:
        orgs = await manager.get_organizations()
        print(len(orgs.organizations))
    finally:
        await IikoCloudApiClientManager.close_all()


if __name__ == "__main__":
    asyncio.run(main())
