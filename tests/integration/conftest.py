"""Фикстуры для интеграционных тестов.

Интеграционные тесты работают в ОДНОМ session-scoped event loop
(loop_scope="session") — это соответствует правилу использования
менеджера «один процесс — один event loop» и не пересоздаёт
сессию iikocloud на каждый тест.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from functools import lru_cache
from uuid import UUID

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from yaml import CSafeLoader as SafeLoader
from yaml import load as yaml_load

from iikocloud import IikoCloudApiClientManager, IikoCloudConfig

logger = logging.getLogger(__name__)

# Роли тестовых серверов — секции верхнего уровня в config.test.yml.
READ = "read"  # стабильный ключ: только read-тесты
WRITE = "write"  # тестовый ключ/стенд: write- и session-тесты

_integration_used = False


def _mark_integration_used() -> None:
    global _integration_used
    _integration_used = True


@lru_cache
def _read_test_config(role: str) -> IikoCloudConfig | None:
    """Прочитать секцию тестового конфига (config.test.yml) для роли.

    Полностью изолировано от боевого config.yml: тесты НИКОГДА не используют
    get_iikocloud_config()/IIKOCLOUD_CONFIG. Кредешелы тестовых серверов
    живут только в файле, путь к которому указан в IIKOCLOUD_TEST_CONFIG.

    Возвращает None (без исключений), если переменная не задана, файла нет
    или в нём отсутствует нужная секция — вызывающий решает, skip это или no-op.

    Кэшируется по роли: файл читается и парсится один раз на роль за процесс.
    Секции без rate_limits валидируются с дефолтами MethodRateLimitsSettings.
    """
    load_dotenv()
    path = os.getenv("IIKOCLOUD_TEST_CONFIG")
    if not path:
        return None
    try:
        with open(path, "rb") as file:
            data = yaml_load(file, Loader=SafeLoader)
    except FileNotFoundError:
        return None
    if not isinstance(data, dict) or role not in data:
        return None
    return IikoCloudConfig.model_validate(data[role])


def load_test_config(role: str) -> IikoCloudConfig:
    """Конфиг тестового сервера для роли или pytest.skip, если его нет."""
    config = _read_test_config(role)
    if config is None:
        pytest.skip(
            f"Нет тестовой конфигурации для роли '{role}'. Задайте "
            f"IIKOCLOUD_TEST_CONFIG и секцию '{role}' в config.test.yml."
        )
    return config


def _section_for(request: pytest.FixtureRequest) -> str:
    """Выбрать сервер по маркеру теста: write/test_server → write, иначе read."""
    node = request.node
    if node.get_closest_marker("write") or node.get_closest_marker("test_server"):
        return WRITE
    return READ


@pytest.fixture
def write_config() -> IikoCloudConfig:
    """Конфиг тестового (write) сервера для тестов, создающих менеджер вручную."""
    return load_test_config(WRITE)


@pytest_asyncio.fixture(loop_scope="session")
async def manager(request: pytest.FixtureRequest) -> IikoCloudApiClientManager:
    """Менеджер для сервера, выбранного по маркеру теста (multitone — переиспользуется).

    write/test_server-тесты → write-секция, остальные → read. Оба ключа могут
    жить одновременно в одном прогоне: multitone ключует инстансы по credentials.

    Не закрывает соединения после теста: экземпляр живёт в session loop
    и переиспользуется. Закрытие — в session-level teardown (_session_teardown).
    """
    _mark_integration_used()
    config = load_test_config(_section_for(request))
    return await IikoCloudApiClientManager.from_config(config)


@pytest_asyncio.fixture(loop_scope="session")
async def fresh_manager(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[IikoCloudApiClientManager, None]:
    """Свежий менеджер: сбрасывает все экземпляры до и после теста.

    Сервер выбирается по маркеру теста (как у manager). Используется для
    тестов токенов/конкурентности, где нужен чистый старт.
    """
    _mark_integration_used()
    await IikoCloudApiClientManager.close_all()

    config = load_test_config(_section_for(request))
    mgr = await IikoCloudApiClientManager.from_config(config)
    yield mgr

    await IikoCloudApiClientManager.close_all()


@pytest_asyncio.fixture(loop_scope="session")
async def organization_id(manager: IikoCloudApiClientManager) -> UUID:
    """Динамический ID первой организации с текущего сервера."""
    resp = await manager.get_organizations()
    if not resp.organizations:
        pytest.skip("Нет доступных организаций")
    return resp.organizations[0].id


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def _session_teardown() -> AsyncGenerator[None, None]:
    """Финальная очистка: закрыть все HTTP-сессии менеджера один раз за session."""
    yield

    if not _integration_used:
        return

    try:
        await IikoCloudApiClientManager.close_all()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Session teardown close_all не удался: %s", exc)
